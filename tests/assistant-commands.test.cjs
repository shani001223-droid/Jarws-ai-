const test = require("node:test");
const assert = require("node:assert/strict");
const commands = require("../assistant-commands.js");

test("normalizes repeated spaces and punctuation", () => {
  assert.equal(commands.normalize("  What   time is it? "), "what time is it");
});

test("recognizes Time button and English time phrases", () => {
  for (const phrase of ["what time is it", "time", "tell me the time", "current time"]) {
    assert.equal(commands.isTimeCommand(phrase), true, phrase);
  }
});

test("recognizes Roman Urdu and Urdu time phrases", () => {
  for (const phrase of ["waqt batao", "abhi kya time hai", "kitne bajay hain", "kitna bajay"]) {
    assert.equal(commands.isTimeCommand(phrase), true, phrase);
  }
  assert.equal(commands.isTimeCommand("وقت بتاؤ"), true);
  assert.equal(commands.isTimeCommand("کتنے بجے ہیں"), true);
});

test("recognizes Date button and English date phrases", () => {
  for (const phrase of ["today's date", "date", "what is the date", "today date"]) {
    assert.equal(commands.isDateCommand(phrase), true, phrase);
  }
});

test("recognizes Roman Urdu and Urdu date phrases", () => {
  for (const phrase of ["tareekh", "tarikh", "aaj ki date", "aaj ki tareekh", "آج کی تاریخ", "تاریخ"]) {
    assert.equal(commands.isDateCommand(phrase), true, phrase);
  }
});

test("does not match unrelated commands", () => {
  assert.equal(commands.isTimeCommand("open Google"), false);
  assert.equal(commands.isDateCommand("who are you"), false);
});
