const RULE_PROVIDERS = {
  acl4ssr_github: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/Ruleset/Github.yaml",
    path: "./providers/acl4ssr-github.yaml",
    interval: 86400,
  },
  acl4ssr_docker: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/Ruleset/Docker.yaml",
    path: "./providers/acl4ssr-docker.yaml",
    interval: 86400,
  },
  acl4ssr_claude: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/Ruleset/Claude.yaml",
    path: "./providers/acl4ssr-claude.yaml",
    interval: 86400,
  },
  acl4ssr_openai: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/Ruleset/OpenAi.yaml",
    path: "./providers/acl4ssr-openai.yaml",
    interval: 86400,
  },
  acl4ssr_gemini: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/Ruleset/Gemini.yaml",
    path: "./providers/acl4ssr-gemini.yaml",
    interval: 86400,
  },
  acl4ssr_bing: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/Ruleset/Bing.yaml",
    path: "./providers/acl4ssr-bing.yaml",
    interval: 86400,
  },
  acl4ssr_banad: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/BanAD.yaml",
    path: "./providers/acl4ssr-banad.yaml",
    interval: 86400,
  },
};

const PREPEND_RULES = [
  "RULE-SET,acl4ssr_banad,REJECT",
  "RULE-SET,acl4ssr_openai,OpenAI",
  "RULE-SET,acl4ssr_claude,OpenAI",
  "RULE-SET,acl4ssr_gemini,OpenAI",
  "RULE-SET,acl4ssr_bing,OpenAI",
  "RULE-SET,acl4ssr_github,Google",
  "RULE-SET,acl4ssr_docker,Google",
];

function main(config, profileName) {
  if (profileName !== "SSRDOG") {
    return config;
  }

  const providers = config["rule-providers"] || {};
  Object.entries(RULE_PROVIDERS).forEach(([key, provider]) => {
    if (!providers[key]) {
      providers[key] = provider;
    }
  });
  config["rule-providers"] = providers;

  const existingRules = Array.isArray(config.rules) ? config.rules : [];
  const newRules = PREPEND_RULES.filter(
    (rule) => !existingRules.includes(rule)
  );
  config.rules = [...newRules, ...existingRules];

  return config;
}
