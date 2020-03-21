/* eslint-env node */

exports.bq_histogram = async (event, context) => {
  console.log(`Event ID: ${context.eventId}`);
  console.log(`Event type: ${context.eventType}`);
  console.log(`Event contents:`, event);
};
