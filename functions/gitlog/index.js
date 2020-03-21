/* eslint-env node */

const stream = require("stream");
// const { PubSub } = require("@google-cloud/pubsub");
const { Storage } = require("@google-cloud/storage");
const git = require("simple-git/promise");
const rimraf = require("rimraf");

// const pubSubClient = new PubSub();

const gitlog = async repo => {
  // const repo = req.query.repo || req.body.repo;
  const localPath = `/tmp/${repo}`;

  // Clone the repo
  try {
    await git().clone(`http://github.com/${repo}.git`, localPath, [
      "--no-checkout",
    ]);
  } catch (err) {
    console.warn("Could not clone repo, was it already cloned?");
    console.error(err);
  }

  // Get and return log
  const { all: commits } = await git(localPath).log([
    `--all`,
    `--no-merges`,
    `--shortstat`,
  ]);

  // Annotate records with the repo
  const records = Array.from(commits).map(el => ({ ...el, repo }));

  // Serialize so we can put in GCS
  const recordString = records.map(rec => JSON.stringify(rec)).join("\n");
  const bufferStream = new stream.PassThrough();
  const buffer = Buffer.from(recordString);

  // Create GCS client
  const storage = new Storage();
  const destinationFile = storage
    .bucket("ghtrends")
    .file(`gitlog/${repo}.json`);

  // Stream it to GCS
  bufferStream
    .end(buffer)
    .pipe(destinationFile.createWriteStream())
    .on("error", err => console.error(err))
    .on("finish", () => console.log("Complete."));

  // Remove the path after we're done
  try {
    rimraf(localPath, err => err && console.error(err));
  } catch (err) {
    console.error(err);
  }
};

exports.gitlog = async (event, context) => {
  console.log(`Event ID: ${context.eventId}`);
  console.log(`Event type: ${context.eventType}`);
  console.log(`Event contents:`, event);
  const { repo } = event;
  await gitlog(repo);
};

// const listen = () => {
//   const subscription = pubSubClient.subscription("ghtrends_gitlog");

//   // Create an event handler to handle messages
//   let messageCount = 0;
//   const messageHandler = message => {
//     console.log(`Received message ${message.id}:`);
//     console.log(`\tData: ${message.data}`);
//     console.log(`\tAttributes: ${message.attributes}`);
//     messageCount += 1;

//     // "Ack" (acknowledge receipt of) the message
//     message.ack();
//   };

//   // Listen for new messages until timeout is hit
//   subscription.on('message', messageHandler);

//   setTimeout(() => {
//     subscription.removeListener('message', messageHandler);
//     console.log(`${messageCount} message(s) received.`);
//   }, timeout * 1000);
// }

// listen();
