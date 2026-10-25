const test = require("node:test");
const assert = require("node:assert/strict");
const parse = require("../reminder-parser.js");

test("parses English reminder with a title before the delay", () => {
  assert.deepEqual(parse("remind me to drink water in 10 minutes"), {
    title: "drink water",
    minutes: 10
  });
});

test("parses English reminder with a delay before the title", () => {
  assert.deepEqual(parse("remind me in 10 minutes to drink water"), {
    title: "drink water",
    minutes: 10
  });
});

test("converts hour units to minutes", () => {
  assert.deepEqual(parse("set a reminder to call mom after 2 hours"), {
    title: "call mom",
    minutes: 120
  });
});

test("parses Roman Urdu duration-first reminder", () => {
  assert.deepEqual(parse("mujhe 10 minute baad pani peene yaad dilao"), {
    title: "pani peene",
    minutes: 10
  });
});

test("parses Roman Urdu title-first reminder", () => {
  assert.deepEqual(parse("pani peena 2 ghante baad yaad dila dena"), {
    title: "pani peena",
    minutes: 120
  });
});

test("rejects reminders outside the seven-day window", () => {
  assert.equal(parse("remind me to water plants in 8 days"), null);
});

test("ignores regular non-reminder messages", () => {
  assert.equal(parse("what is the weather today"), null);
});
