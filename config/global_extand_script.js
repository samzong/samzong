// IT'S working on CVR 2.4.3

const RULE_PROVIDERS = {
  acl4ssr_github: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/Ruleset/Github.yaml",
    path: "./providers/acl4ssr-github.yaml",
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
  acl4ssr_banad: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Providers/BanAD.yaml",
    path: "./providers/acl4ssr-banad.yaml",
    interval: 86400,
  },
  xptv_direct: {
    type: "http",
    behavior: "classical",
    url: "https://raw.githubusercontent.com/fangkuia/XPTV/main/X/clash.yaml",
    path: "./providers/xptv-direct.yaml",
    interval: 86400,
  },
};

const GLOBAL_KEYWORDS = ["Google", "节点选择", "PROXIES", "Global", "GLOBAL", "PROXY"];

function resolveTargetGroup(groups, keywords) {
  if (!groups || !Array.isArray(groups) || groups.length === 0) return "DIRECT";
  for (const kw of keywords) {
    const match = groups.find((g) => g.name && g.name.toLowerCase().includes(kw.toLowerCase()));
    if (match) return match.name;
  }
  return groups[0].name;
}

function buildRegionGroup(config, groupName, regionRegex, fallbackGroups) {
  const proxies = (config.proxies || [])
    .filter((p) => p.name && regionRegex.test(p.name))
    .map((p) => p.name);

  if (proxies.length === 0) {
    return resolveTargetGroup(config["proxy-groups"], fallbackGroups);
  }

  if (!config["proxy-groups"]) config["proxy-groups"] = [];

  config["proxy-groups"].unshift({
    name: groupName,
    type: "select",
    proxies: proxies,
  });

  return groupName;
}

function main(config, profileName) {
  const providers = config["rule-providers"] || {};
  Object.entries(RULE_PROVIDERS).forEach(([key, provider]) => {
    if (!providers[key]) providers[key] = provider;
  });
  config["rule-providers"] = providers;

  const groupUS = buildRegionGroup(config, "US", /美国|US|United States|🇺🇸/i, ["OpenAI", "PROXY"]);
  // const groupSG = buildRegionGroup(config, "SG", /新加坡|SG|Singapore|🇸🇬/i, ["Singapore", "PROXY"]);
  const groupJP = buildRegionGroup(config, "JP", /日本|JP|Japan|🇯🇵/i, ["Japan", "PROXY"]);

  const targetGlobal = resolveTargetGroup(config["proxy-groups"], GLOBAL_KEYWORDS);

  const customRules = {
    "DOMAIN-SUFFIX": {
      "claude.com": groupUS,
      "anthropic.com": groupUS,
      "openai.com": groupUS,
      "chatgpt.com": groupUS,
      "oaistatic.com": groupUS,
      "oaiusercontent.com": groupUS,
      "gemini.google.com": groupUS,
      "generativelanguage.googleapis.com": groupUS,
      "linkedin.cn": targetGlobal,
      "linkedin.com": targetGlobal,
      "licdn.com": targetGlobal,
      "x.com": groupUS,
      "twitter.com": groupUS,
      "linux.do": groupJP,
    },
    "RULE-SET": {
      "xptv_direct": "DIRECT",
      "acl4ssr_banad": "REJECT",
      "acl4ssr_openai": groupUS,
      "acl4ssr_claude": groupUS,
      "acl4ssr_gemini": groupUS,
      "acl4ssr_github": groupUS,
    },
    "IP-CIDR": {
      "58.240.226.242/32": "DIRECT",
    }
  };

  const rules = [];
  for (const [type, mappings] of Object.entries(customRules)) {
    for (const [value, target] of Object.entries(mappings)) {
      rules.push(`${type},${value},${target}`);
    }
  }

  const existing = config.rules || [];
  config.rules = [...rules.filter((r) => !existing.includes(r)), ...existing];

  config.dns = config.dns || {};
  config.dns["nameserver-policy"] = config.dns["nameserver-policy"] || {};

  const customDNS = {
    "10.64.46.101": [
      "*.daocloud.io",
      "*.daocloud.cn"
    ]
  };

  Object.entries(customDNS).forEach(([server, domains]) => {
    domains.forEach((domain) => {
      config.dns["nameserver-policy"][domain] = server;
    });
  });

  return config;
}
