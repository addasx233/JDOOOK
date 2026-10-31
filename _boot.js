const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const MASTER = Buffer.from("9f3c1a07e6b84d52c0a17e93f4d68b2055ac91e7d03b6f48a2c91d70e5b34f18", "hex");
const ROOT = __dirname;

function derive(label) {
  return crypto.createHmac("sha256", MASTER).update(label).digest();
}

function decrypt(file) {
  const rel = path.relative(ROOT, file).split(path.sep).join("/");
  const blob = fs.readFileSync(path.join(ROOT, "_payload", rel + ".bin"));
  const nonce = blob.subarray(0, 16);
  const tag = blob.subarray(16, 48);
  const ciphertext = blob.subarray(48);
  const macKey = derive("mac");
  const expect = crypto.createHmac("sha256", macKey).update(nonce).update(ciphertext).digest();
  if (tag.length !== expect.length || !crypto.timingSafeEqual(tag, expect)) {
    throw new Error("密文校验失败");
  }
  const decipher = crypto.createDecipheriv("aes-256-ctr", derive("enc"), nonce);
  return Buffer.concat([decipher.update(ciphertext), decipher.final()]).toString("utf8");
}

module.exports = { decrypt };
