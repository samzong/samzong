// Define main function (script entry)
const ssrPrependRule = [
  "DOMAIN-SUFFIX,meta.com,OpenAI",
  "DOMAIN-SUFFIX,meta.ai,OpenAI",
  "DOMAIN-SUFFIX,facebook.com,OpenAI",
  "DOMAIN-SUFFIX,fbcdn.net,OpenAI",
  "DOMAIN-SUFFIX,oaiusercontent.com,OpenAI",
  "DOMAIN-SUFFIX,copilot.microsoft.com,OpenAI",
  "DOMAIN-SUFFIX,cdn.oaistatic.com,OpenAI",
  "DOMAIN-SUFFIX,googlevideo.com,'🇨🇳 Taiwan'",
  "DOMAIN-SUFFIX,youtube.com,'🇨🇳 Taiwan'",
  "DOMAIN-SUFFIX,gemini.google.com,OpenAI",
  "DOMAIN-SUFFIX,google.com,OpenAI",
  "DOMAIN-SUFFIX,openai.com,OpenAI",
];
function main(config) {
  let oldrules = config["rules"];
  config["rules"] = ssrPrependRule.concat(oldrules);
  return config;
}
