/* eslint-env mocha */

const proxyquire = require("proxyquire");
const sinon = require("sinon");
const assert = require("assert");
const { ObjectWritableMock } = require("stream-mock");
const { Storage } = require("@google-cloud/storage");
const git = require("simple-git/promise");
const rimraf = require("rimraf");

const { gitlog } = require("..");

const makeStubs = () => {
  sinon.stub(console, `log`);
  // sinon.createStubInstance(git, {
  //   clone: sinon.stub(),
  //   log: sinon.stub().returns({ all: [{ key: "value" }] }),
  // });
  // sinon.createStubInstance(Storage, {
  //   bucket: () => ({
  //     file: () => ({
  //       createWriteStream: () => new ObjectWritableMock(),
  //     }),
  //   }),
  // });
  // sinon.createStubInstance(rimraf);
};

const removeStubs = () => {
  console.log.restore();
};

beforeEach(makeStubs);
afterEach(removeStubs);

describe("gitlog", () => {
  it("prints the passed data", async () => {
    const repo = "axios/axios";
    const event = {
      data: repo,
    };

    // Call tested function and verify its behavior
    await gitlog(event, { eventId: 0, eventType: 0 });

    assert.strictEqual(console.log.calledWith(`Event contents:`, event), true);
  });
});
