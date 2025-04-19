// ==UserScript==
// @name         Twitter Filter
// @namespace    http://tampermonkey.net/
// @version      0.1
// @description  Filter tweets using local API
// @author       You
// @match        https://twitter.com/*
// @match        https://x.com/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    console.log('🚀 Twitter Filter Script Loaded');

    class Node {
        constructor(key, value) {
            this.key = key;
            this.value = value;
            this.prev = null;
            this.next = null;
            this.timestamp = Date.now();
        }
    }

    class LRUCache {
        constructor(maxSize = 500) {
            this.maxSize = maxSize;
            this.size = 0;
            this.cache = new Map();
            this.head = null;
            this.tail = null;
            this.loadFromStorage();
            console.log('📦 LRU Cache initialized with size:', maxSize);
        }

        saveToStorage() {
            const cacheData = {
                items: Array.from(this.cache.entries()).map(([key, node]) => ({
                    key,
                    value: node.value,
                    timestamp: node.timestamp
                }))
            };
            try {
                localStorage.setItem('twitterFilterCache', JSON.stringify(cacheData));
            } catch (e) {
                console.error('Failed to save cache to storage:', e);
            }
        }

        loadFromStorage() {
            try {
                const data = localStorage.getItem('twitterFilterCache');
                if (data) {
                    const cacheData = JSON.parse(data);
                    cacheData.items.forEach(item => {
                        if (Date.now() - item.timestamp < 24 * 60 * 60 * 1000) {
                            this.set(item.key, item.value);
                        }
                    });
                }
            } catch (e) {
                console.error('Failed to load cache from storage:', e);
            }
        }

        addToFront(node) {
            node.prev = null;
            node.next = null;

            if (!this.head) {
                this.head = node;
                this.tail = node;
            } else {
                node.next = this.head;
                this.head.prev = node;
                this.head = node;
            }
        }

        removeNode(node) {
            if (node === this.head) {
                this.head = node.next;
            }
            if (node === this.tail) {
                this.tail = node.prev;
            }
            if (node.prev) {
                node.prev.next = node.next;
            }
            if (node.next) {
                node.next.prev = node.prev;
            }
            node.prev = null;
            node.next = null;
        }

        moveToFront(node) {
            if (node === this.head) return;
            this.removeNode(node);
            this.addToFront(node);
        }

        removeLRU() {
            if (!this.tail) return;
            const key = this.tail.key;
            this.removeNode(this.tail);
            this.cache.delete(key);
            this.size--;
        }

        get(key) {
            const node = this.cache.get(key);
            if (!node) return null;
            this.moveToFront(node);
            return node.value;
        }

        has(key) {
            return this.cache.has(key);
        }

        set(key, value) {
            const existingNode = this.cache.get(key);

            if (existingNode) {
                existingNode.value = value;
                existingNode.timestamp = Date.now();
                this.moveToFront(existingNode);
            } else {
                if (this.size >= this.maxSize) {
                    this.removeLRU();
                }

                const newNode = new Node(key, value);
                this.cache.set(key, newNode);
                this.addToFront(newNode);
                this.size++;
            }

            this.saveToStorage();
        }

        clear() {
            this.cache = new Map();
            this.head = null;
            this.tail = null;
            this.size = 0;
            localStorage.removeItem('twitterFilterCache');
        }

        getStats() {
            return {
                size: this.size,
                maxSize: this.maxSize,
                head: this.head?.key?.slice(0, 20),
                tail: this.tail?.key?.slice(0, 20)
            };
        }
    }

    const loadProcessedTweets = () => {
        try {
            const data = localStorage.getItem('twitterFilterProcessed');
            return data ? new Set(JSON.parse(data)) : new Set();
        } catch (e) {
            return new Set();
        }
    };

    const saveProcessedTweets = (tweets) => {
        try {
            localStorage.setItem('twitterFilterProcessed',
                JSON.stringify(Array.from(tweets)));
        } catch (e) {
            console.error('Failed to save processed tweets:', e);
        }
    };

    function extractTweetDetails(tweet) {
        // Find tweet URL using analytics link
        const analyticsLink = tweet.querySelector('a[href*="/analytics"]');
        let tweetId = '';
        let tweetUrl = '';
        let username = '';
        
        if (analyticsLink) {
            const href = analyticsLink.getAttribute('href');
            const matches = href.match(/\/status\/(\d+)\/analytics/);
            if (matches && matches[1]) {
                tweetId = matches[1];
                // Find username from User-Name testid
                const userElement = tweet.querySelector('div[data-testid="User-Name"]');
                if (userElement) {
                    const usernameElement = userElement.querySelector('div[dir="ltr"] span span');
                    if (usernameElement) {
                        username = usernameElement.textContent.replace('@', '');
                        tweetUrl = `https://twitter.com/${username}/status/${tweetId}`;
                    }
                }
            }
        }

        const textElement = tweet.querySelector('div[data-testid="tweetText"]');
        const tweet_text = textElement ? textElement.textContent : '';

        return {
            id: tweetId,
            url: tweetUrl,
            username: username,
            text: tweet_text
        };
    }

    const tweet_cache = new LRUCache(500);
    let apiCallCount = parseInt(localStorage.getItem('twitterFilterApiCalls') || '0');
    let lastProcessedTime = 0;
    const processedTweets = loadProcessedTweets();

    function getTweetId(tweet) {
        const details = extractTweetDetails(tweet);
        return details.url || details.id || `${details.username}:${details.text}`;
    }

    async function callAPI(tweet_text, tweet_details) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'POST',
                url: 'http://127.0.0.1:8000/completion',
                headers: {
                    'Content-Type': 'application/json'
                },
                data: JSON.stringify({
                    prompt: tweet_text,
                    tweet_url: tweet_details.url,
                    user_name: tweet_details.username
                }),
                onload: function(response) {
                    try {
                        const result = JSON.parse(response.responseText);
                        resolve({ ok: true, data: result });
                    } catch (e) {
                        reject(new Error('Failed to parse response'));
                    }
                },
                onerror: function(error) {
                    reject(error);
                }
            });
        });
    }

    async function processTweets() {
        const now = Date.now();
        if (now - lastProcessedTime < 1000) return;
        lastProcessedTime = now;

        const tweetSelector = 'article[data-testid="tweet"]';
        const tweets = document.querySelectorAll(tweetSelector);

        console.log(`📥 Found ${tweets.length} tweets to process`);

        for(const tweet of tweets) {
            const tweetDetails = extractTweetDetails(tweet);
            const tweetId = getTweetId(tweet);
            const textElement = tweet.querySelector('div[data-testid="tweetText"]');

            if (!textElement || processedTweets.has(tweetId)) {
                if (processedTweets.has(tweetId)) {
                    console.log('⏩ Already processed:', tweetId.slice(0, 50));
                }
                continue;
            }

            const tweet_text = textElement.textContent;
            const tweet_user = tweetDetails.username;

            if(tweet_cache.has(tweetId)) {
                console.log('🔵 Cache hit:', tweet_text.slice(0, 50));
                const cachedResult = tweet_cache.get(tweetId);
                if (cachedResult && cachedResult.hidden) {
                    tweet.style.display = 'none';
                }
                continue;
            }

            try {
                console.log('🟡 Calling API for tweet:', tweet_text.slice(0, 50));
                apiCallCount++;
                localStorage.setItem('twitterFilterApiCalls', apiCallCount.toString());

                const response = await callAPI(tweet_text, tweetDetails);
                console.log('🟢 API Response:', response.data);

                const shouldHide = response.data && response.data.decision === 'NO';
                if (shouldHide) {
                    tweet.style.display = 'none';
                }

                tweet_cache.set(tweetId, {
                    text: tweet_text,
                    tweet_user: tweet_user,
                    url: tweetDetails.url,
                    processed: true,
                    timestamp: Date.now(),
                    success: response.ok,
                    result: response.data,
                    hidden: shouldHide
                });

                processedTweets.add(tweetId);
                saveProcessedTweets(processedTweets);

            } catch(error) {
                console.error('🔴 Error processing tweet:', error);
                tweet_cache.set(tweetId, {
                    text: tweet_text,
                    tweet_user: tweet_user,
                    url: tweetDetails.url,
                    processed: true,
                    timestamp: Date.now(),
                    error: true
                });
                processedTweets.add(tweetId);
                saveProcessedTweets(processedTweets);
            }
        }
    }

    function startObserving() {
        const timeline = document.querySelector('div[data-testid="primaryColumn"]');

        if (timeline) {
            console.log('🎯 Found timeline, starting observation');

            const observer = new MutationObserver((mutations) => {
                const relevantMutations = mutations.filter(m => m.addedNodes.length > 0);
                if (relevantMutations.length > 0) {
                    console.log(`👀 Detected ${relevantMutations.length} mutations with new nodes`);
                    processTweets();
                }
            });

            observer.observe(timeline, {
                childList: true,
                subtree: true
            });

            console.log('✅ Timeline observation started');
            processTweets();
        } else {
            console.log('⏳ Timeline not found, retrying in 1 second...');
            setTimeout(startObserving, 1000);
        }
    }

    if (document.readyState === 'complete') {
        startObserving();
    } else {
        window.addEventListener('load', startObserving);
    }

    window.twitterFilter = {
        cache: tweet_cache,
        processedSet: processedTweets,
        process: processTweets,
        apiCalls: () => apiCallCount,
        stats: () => ({
            cacheSize: tweet_cache.size,
            processedTweets: processedTweets.size,
            apiCalls: apiCallCount,
            ...tweet_cache.getStats()
        }),
        recheck: () => {
            console.log('🔄 Manually rechecking tweets...');
            processTweets();
        },
        clearCache: () => {
            tweet_cache.clear();
            processedTweets.clear();
            localStorage.clear();
            apiCallCount = 0;
            console.log('🧹 Cache cleared');
        }
    };
})();