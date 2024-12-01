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

    // Node class for doubly linked list
    class Node {
        constructor(key, value) {
            this.key = key;
            this.value = value;
            this.prev = null;
            this.next = null;
            this.timestamp = Date.now();
        }
    }

    // Custom LRU Cache implementation
    class LRUCache {
        constructor(maxSize = 500) {
            this.maxSize = maxSize;
            this.size = 0;
            this.cache = new Map();
            this.head = null;
            this.tail = null;
            console.log('📦 LRU Cache initialized with size:', maxSize);
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

    // Initialize cache and counters
    const tweet_cache = new LRUCache(500);
    let apiCallCount = 0;
    let lastProcessedTime = 0;

    // API call function using GM_xmlhttpRequest
    async function callAPI(tweet_text) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: 'POST',
                url: 'http://localhost:8000/completion',
                headers: {
                    'Content-Type': 'application/json'
                },
                data: JSON.stringify({
                    prompt: tweet_text
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

    // Process tweets function
    async function processTweets() {
        const now = Date.now();
        if (now - lastProcessedTime < 1000) return;
        lastProcessedTime = now;

        const tweetSelector = 'article[data-testid="tweet"]';
        const tweets = document.querySelectorAll(tweetSelector);

        console.log(`📥 Found ${tweets.length} tweets to process`);

        for(const tweet of tweets) {
            const textElement = tweet.querySelector('div[data-testid="tweetText"]');
            if (!textElement) continue;

            const tweet_text = textElement.textContent;

            if(tweet_cache.has(tweet_text)) {
                console.log('🔵 Cache hit:', tweet_text.slice(0, 50));
                continue;
            }

            try {
                console.log('🟡 Calling API for tweet:', tweet_text.slice(0, 50));
                apiCallCount++;

                const response = await callAPI(tweet_text);
                console.log('🟢 API Response:', response.data);

                // Handle the API response
                if (response.data && response.data.decision === 'NO') {
                    // Hide the tweet if the API says NO
                    tweet.style.display = 'none';
                }

                tweet_cache.set(tweet_text, {
                    processed: true,
                    timestamp: Date.now(),
                    success: response.ok,
                    result: response.data,
                    hidden: response.data.decision === 'NO'
                });

            } catch(error) {
                console.error('🔴 Error processing tweet:', error);
                tweet_cache.set(tweet_text, {
                    processed: true,
                    timestamp: Date.now(),
                    error: true
                });
            }
        }
    }

    // Function to start observing timeline
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

    // Initialize after page load
    if (document.readyState === 'complete') {
        startObserving();
    } else {
        window.addEventListener('load', startObserving);
    }

    // Add debug interface
    window.twitterFilter = {
        cache: tweet_cache,
        process: processTweets,
        apiCalls: () => apiCallCount,
        stats: () => tweet_cache.getStats(),
        recheck: () => {
            console.log('🔄 Manually rechecking tweets...');
            processTweets();
        }
    };

})();