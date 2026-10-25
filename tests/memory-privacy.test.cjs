const test = require("node:test");
const assert = require("node:assert/strict");
const { looksSensitive } = require("../memory-privacy.js");

test("does not flag ordinary conversation", () => {
  for (const text of [
    "Mujhe aaj bohat udaas lag raha hai.",
    "Remember that I prefer short Roman Urdu answers.",
    "Remind me in 10 minutes.",
    "I am excited to work on HOSHI."
  ]) assert.equal(looksSensitive(text), false, text);
});

test("filters credential and authentication language", () => {
  for (const text of [
    "My password is not for storage.",
    "api_key=sk-abcdefghijklmnopqrstuv",
    "Use this Bearer eyJhbGciOiJIUzI1NiJ9.abc.def",
    "Here is my GitHub token: ghp_abcdefghijklmnopqrstuvwxyz123456",
    "-----BEGIN PRIVATE KEY-----"
  ]) assert.equal(looksSensitive(text), true, text);
});

test("filters OTPs, long numeric strings, phone numbers and email addresses", () => {
  for (const text of [
    "My OTP is 778899.",
    "My account reference is 12345678.",
    "Call me at +92 300 1234567.",
    "Write to shani@example.com."
  ]) assert.equal(looksSensitive(text), true, text);
});

test("filters seed/recovery phrase disclosures", () => {
  assert.equal(looksSensitive("My seed phrase is written down."), true);
  assert.equal(looksSensitive("I might need a recovery phrase."), true);
});
