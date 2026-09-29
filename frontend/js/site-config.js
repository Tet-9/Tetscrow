// One place for every outside link on the site. Fill these in when you have them.
// Empty string = the button shows a friendly "coming soon" message instead of a dead link.
window.TET_SITE = {
  email: "admin@tet.io", // change to your real contact email
  links: {
    gitbook: "",     // Docs nav link, footer "Gitbook"
    docs: "",        // optional; falls back to gitbook when empty
    pitchDeck: "",   // footer "Pitch Deck"
    twitter: "",     // footer "Twitter" + hero icon
    telegram: "",    // footer "Telegram" + hero icon
    youtube: "",     // footer "YouTube" + hero icon
    video: "",       // "Watch A Video" button in How Tet Works
    dextools: "",    // DEXTools page for your pair, once listed
    coinmarketcap: "" // CoinMarketCap page, once listed
  },
  // Real press coverage only. Example item:
  // { source: "Coinpedia", title: "How Tet guarantees security", url: "https://..." }
  press: [
    { scene: "shield",   art: "Trust",                  vertical: "DECENTRALIZED ESCROW", title: "Tet beta testing begins",              url: "" },
    { scene: "rocket",   art: "Innovating the future",  title: "Tet unveils its Web3 escrow platform",   url: "" },
    { scene: "computer", art: "Behind the Tech",        title: "Security and transparency by design",    url: "" },
    { scene: "globe",    art: "Revolutionizing Escrow", title: "Tet brings escrow on-chain",             url: "" }
  ]
};
