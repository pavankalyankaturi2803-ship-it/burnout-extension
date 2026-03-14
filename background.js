let siteUsage = {};

const limits = {
    "www.youtube.com": 120,
    "youtube.com": 120,
    "www.instagram.com": 120,
    "instagram.com": 120,
    "www.facebook.com": 1200,
    "facebook.com": 1200,
    "mail.google.com": 1200
};

function checkActiveTab() {

    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {

        if (!tabs[0] || !tabs[0].url) return;

        try {

            let url = new URL(tabs[0].url);
            let site = url.hostname;

            if (!(site in limits)) return;

            if (!siteUsage[site]) {
                siteUsage[site] = 0;
            }

            siteUsage[site] += 1;

            console.log(site, "time:", siteUsage[site]);

            if (siteUsage[site] >= limits[site]) {

                chrome.tabs.update(tabs[0].id, {
                    url: chrome.runtime.getURL("block.html")
                });

            }

        } catch(e) {}

    });

}

setInterval(checkActiveTab, 1000);
