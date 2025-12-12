// API Configuration
const API_URL = 'http://localhost:5000/api';

// ==================== Utility Functions ====================
const apiCall = async (endpoint, method = 'GET', data = null) => {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
    };
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    try {
        console.log(`API Call: ${method} ${API_URL}${endpoint}`, data);
        const response = await fetch(`${API_URL}${endpoint}`, options);
        const responseData = await response.json();
        console.log(`API Response: ${response.status}`, responseData);
        return { success: response.ok, data: responseData, status: response.status };
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, error: error.message };
    }
};

// ==================== React Components ====================

// Login/Register Page Component
const AuthPage = ({ onAuthSuccess }) => {
    const [isLogin, setIsLogin] = React.useState(true);
    const [formData, setFormData] = React.useState({ username: '', email: '', password: '' });
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState('');

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const endpoint = isLogin ? '/auth/login' : '/auth/register';
        const result = await apiCall(endpoint, 'POST', formData);

        if (result.success) {
            localStorage.setItem('token', result.data.token);
            localStorage.setItem('user', JSON.stringify(result.data.user));
            onAuthSuccess(result.data.user);
        } else {
            setError(result.data.error || 'An error occurred');
        }
        setLoading(false);
    };

    return React.createElement('div', { className: 'auth-container' },
        React.createElement('div', { className: 'auth-form' },
            React.createElement('h1', { className: 'gradient-text text-3xl font-bold mb-6 text-center' },
                isLogin ? 'Welcome Back' : 'Create Account'
            ),
            React.createElement('form', { onSubmit: handleSubmit },
                !isLogin && React.createElement('div', { className: 'floating-label mb-6' },
                    React.createElement('input', {
                        type: 'text',
                        name: 'username',
                        value: formData.username,
                        onChange: handleChange,
                        placeholder: ' ',
                        required: true,
                    }),
                    React.createElement('label', {}, 'Username')
                ),
                React.createElement('div', { className: 'floating-label mb-6' },
                    React.createElement('input', {
                        type: 'email',
                        name: 'email',
                        value: formData.email,
                        onChange: handleChange,
                        placeholder: ' ',
                        required: true,
                    }),
                    React.createElement('label', {}, 'Email')
                ),
                React.createElement('div', { className: 'floating-label mb-6' },
                    React.createElement('input', {
                        type: 'password',
                        name: 'password',
                        value: formData.password,
                        onChange: handleChange,
                        placeholder: ' ',
                        required: true,
                    }),
                    React.createElement('label', {}, 'Password')
                ),
                error && React.createElement('p', { className: 'text-red-500 text-sm mb-4' }, error),
                React.createElement('button', {
                    type: 'submit',
                    className: 'gradient-btn w-full mb-4',
                    disabled: loading,
                },
                    loading ? 'Loading...' : isLogin ? 'Login' : 'Register'
                ),
            ),
            React.createElement('p', { className: 'text-center text-sm text-gray-400 mt-4' },
                isLogin ? "Don't have an account? " : 'Already have an account? ',
                React.createElement('button', {
                    onClick: () => {
                        setIsLogin(!isLogin);
                        setError('');
                        setFormData({ username: '', email: '', password: '' });
                    },
                    className: 'text-cyan-400 cursor-pointer font-semibold hover:text-cyan-300',
                },
                    isLogin ? 'Register' : 'Login'
                )
            )
        )
    );
};

// Dashboard Component  
const Dashboard = ({ user, onLogout }) => {
    const [activeTab, setActiveTab] = React.useState('overview');
    const [accounts, setAccounts] = React.useState([]);
    const [posts, setPosts] = React.useState([]);
    const [insights, setInsights] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState('');
    const [showConnectModal, setShowConnectModal] = React.useState(false);
    const [selectedPlatform, setSelectedPlatform] = React.useState('');
    const [accountName, setAccountName] = React.useState('');
    const [connecting, setConnecting] = React.useState(false);
    const [hashtagData, setHashtagData] = React.useState(null);
    const [audienceData, setAudienceData] = React.useState(null);
    const [competitorData, setCompetitorData] = React.useState(null);
    const [anomalies, setAnomalies] = React.useState(null);
    const [forecast, setForecast] = React.useState(null);
    const [contentCalendar, setContentCalendar] = React.useState(null);
    const [engagementPrediction, setEngagementPrediction] = React.useState(null);
    const [predictionContent, setPredictionContent] = React.useState('');

    const platforms = [
        { name: 'Instagram', icon: '📷', id: 'instagram' },
        { name: 'Facebook', icon: '👥', id: 'facebook' },
        { name: 'Twitter', icon: '🐦', id: 'twitter' },
        { name: 'LinkedIn', icon: '💼', id: 'linkedin' },
        { name: 'TikTok', icon: '🎵', id: 'tiktok' },
        { name: 'YouTube', icon: '📺', id: 'youtube' },
    ];

    React.useEffect(() => {
        loadDashboardData();
    }, []);

    const loadDashboardData = async () => {
        setLoading(true);
        setError('');
        try {
            const [accountsRes, postsRes, insightsRes] = await Promise.all([
                apiCall('/accounts'),
                apiCall('/posts'),
                apiCall('/insights'),
            ]);

            if (accountsRes.success) setAccounts(accountsRes.data.accounts || []);
            else setAccounts([]);
            
            if (postsRes.success) setPosts(postsRes.data.posts || []);
            else setPosts([]);
            
            if (insightsRes.success) setInsights(insightsRes.data.insights || []);
            else setInsights([]);
        } catch (err) {
            console.error('Error:', err);
            setError('Failed to load data');
        }
        setLoading(false);
    };

    const loadHashtagData = async () => {
        const result = await apiCall('/analytics/hashtags');
        if (result.success) setHashtagData(result.data);
    };

    const loadAudienceInsights = async () => {
        const result = await apiCall('/analytics/audience-insights');
        if (result.success) setAudienceData(result.data);
    };

    const loadCompetitorAnalysis = async () => {
        const result = await apiCall('/analytics/competitor-analysis');
        if (result.success) setCompetitorData(result.data);
    };

    const loadAnomalies = async () => {
        const result = await apiCall('/analytics/anomalies');
        if (result.success) setAnomalies(result.data);
    };

    const loadForecast = async () => {
        const result = await apiCall('/analytics/forecast?months=3');
        if (result.success) setForecast(result.data);
    };

    const loadContentCalendar = async () => {
        const result = await apiCall('/analytics/content-calendar');
        if (result.success) setContentCalendar(result.data);
    };

    const handlePredictEngagement = async () => {
        if (!predictionContent.trim()) {
            alert('Enter some content to predict engagement');
            return;
        }
        const result = await apiCall('/analytics/predict-engagement', 'POST', {
            content: predictionContent,
            platform: 'instagram'
        });
        if (result.success) setEngagementPrediction(result.data);
    };

    const handleConnectAccount = async () => {
        if (!selectedPlatform || !accountName.trim()) {
            alert('Please select a platform and enter an account name');
            return;
        }

        setConnecting(true);
        const result = await apiCall('/accounts/connect', 'POST', {
            platform: selectedPlatform,
            account_name: accountName.trim()
        });

        if (result.success) {
            alert('Account connected successfully!');
            setShowConnectModal(false);
            setSelectedPlatform('');
            setAccountName('');
            loadDashboardData();
        } else {
            alert('Error: ' + (result.data.error || 'Failed to connect account'));
        }
        setConnecting(false);
    };

    const handleDisconnectAccount = async (accountId) => {
        if (!confirm('Are you sure you want to disconnect this account?')) return;

        const result = await apiCall(`/accounts/${accountId}`, 'DELETE');
        if (result.success) {
            alert('Account disconnected');
            loadDashboardData();
        } else {
            alert('Error: ' + (result.data.error || 'Failed to disconnect'));
        }
    };

    if (loading) {
        return React.createElement('div', { className: 'flex items-center justify-center min-h-screen bg-gray-900' },
            React.createElement('div', { className: 'text-center' },
                React.createElement('div', { className: 'text-2xl gradient-text font-bold animate-pulse' }, 'Loading Dashboard...')
            )
        );
    }

    return React.createElement('div', { className: 'dashboard-container' },
        // Connect Account Modal
        showConnectModal && React.createElement('div', { className: 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50' },
            React.createElement('div', { className: 'bg-gray-800 rounded-lg p-8 max-w-md w-full' },
                React.createElement('h3', { className: 'text-2xl font-bold mb-6 text-cyan-400' }, 'Connect Social Account'),
                
                React.createElement('div', { className: 'mb-6' },
                    React.createElement('label', { className: 'block text-sm font-semibold mb-3 text-gray-300' }, 'Select Platform:'),
                    React.createElement('div', { className: 'grid grid-cols-3 gap-2' },
                        platforms.map(p => React.createElement('button', {
                            key: p.id,
                            className: `p-4 rounded border-2 transition ${selectedPlatform === p.id ? 'border-cyan-400 bg-cyan-400 bg-opacity-20' : 'border-gray-600 hover:border-cyan-400'}`,
                            onClick: () => setSelectedPlatform(p.id)
                        },
                            React.createElement('div', { className: 'text-2xl' }, p.icon),
                            React.createElement('div', { className: 'text-xs mt-1' }, p.name)
                        ))
                    )
                ),

                React.createElement('div', { className: 'mb-6' },
                    React.createElement('label', { className: 'block text-sm font-semibold mb-2 text-gray-300' }, 'Account Name/Username:'),
                    React.createElement('input', {
                        type: 'text',
                        value: accountName,
                        onChange: (e) => setAccountName(e.target.value),
                        placeholder: 'e.g., @username or account_name',
                        className: 'w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400'
                    })
                ),

                React.createElement('div', { className: 'flex gap-3' },
                    React.createElement('button', {
                        onClick: handleConnectAccount,
                        disabled: connecting,
                        className: 'flex-1 bg-cyan-500 hover:bg-cyan-600 text-white font-bold py-2 px-4 rounded disabled:opacity-50'
                    }, connecting ? 'Connecting...' : 'Connect'),
                    React.createElement('button', {
                        onClick: () => {
                            setShowConnectModal(false);
                            setSelectedPlatform('');
                            setAccountName('');
                        },
                        className: 'flex-1 bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded'
                    }, 'Cancel')
                )
            )
        ),

        React.createElement('div', { className: 'sidebar' },
            React.createElement('h2', { className: 'gradient-text text-xl font-bold mb-6' }, 'Analytics Hub'),
            ['overview', 'accounts', 'hashtags', 'audience', 'competitor', 'predict', 'anomalies', 'forecast', 'calendar', 'insights', 'recommendations'].map(tab => {
                const tabIcons = {
                    'overview': '📊', 'accounts': '🔗', 'hashtags': '#️⃣', 'audience': '👥',
                    'competitor': '⚔️', 'predict': '🎯', 'anomalies': '⚡', 'forecast': '📈',
                    'calendar': '📅', 'insights': '🧠', 'recommendations': '💡'
                };
                return React.createElement('div', {
                    key: tab,
                    className: `sidebar-item ${activeTab === tab ? 'active' : ''}`,
                    onClick: () => {
                        setActiveTab(tab);
                        if (tab === 'hashtags' && !hashtagData) loadHashtagData();
                        if (tab === 'audience' && !audienceData) loadAudienceInsights();
                        if (tab === 'competitor' && !competitorData) loadCompetitorAnalysis();
                        if (tab === 'anomalies' && !anomalies) loadAnomalies();
                        if (tab === 'forecast' && !forecast) loadForecast();
                        if (tab === 'calendar' && !contentCalendar) loadContentCalendar();
                    }
                },
                    React.createElement('span', { className: 'mr-2' }, tabIcons[tab]),
                    tab.charAt(0).toUpperCase() + tab.slice(1)
                );
            })
        ),

        React.createElement('div', { className: 'main-content' },
            React.createElement('div', { className: 'navbar' },
                React.createElement('div', { className: 'navbar-brand' }, '📈 AI Analytics Platform'),
                React.createElement('div', {}, '👤 ' + user.username),
                React.createElement('button', { className: 'text-red-400 ml-4', onClick: onLogout }, 'Logout')
            ),
            React.createElement('div', { className: 'p-6 overflow-y-auto' },
                error && React.createElement('div', { className: 'bg-red-500 text-white p-4 rounded mb-4' }, error),
                
                activeTab === 'overview' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, 'Dashboard'),
                    React.createElement('div', { className: 'grid grid-cols-4 gap-4' },
                        React.createElement('div', { className: 'card' },
                            React.createElement('div', { className: 'card-label' }, 'Total Posts'),
                            React.createElement('div', { className: 'card-value' }, posts.length)
                        ),
                        React.createElement('div', { className: 'card' },
                            React.createElement('div', { className: 'card-label' }, 'Connected'),
                            React.createElement('div', { className: 'card-value' }, accounts.length)
                        ),
                        React.createElement('div', { className: 'card' },
                            React.createElement('div', { className: 'card-label' }, 'Total Likes'),
                            React.createElement('div', { className: 'card-value' }, posts.reduce((sum, p) => sum + (p.likes || 0), 0))
                        ),
                        React.createElement('div', { className: 'card' },
                            React.createElement('div', { className: 'card-label' }, 'Engagement'),
                            React.createElement('div', { className: 'card-value' }, posts.length ? Math.round(posts.reduce((s, p) => s + (p.likes || 0), 0) / posts.length) : 0)
                        )
                    )
                ),

                activeTab === 'accounts' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, 'Connected Accounts'),
                    React.createElement('button', {
                        onClick: () => setShowConnectModal(true),
                        className: 'gradient-btn mb-6'
                    }, '+ Connect New Account'),
                    
                    accounts.length > 0 ? React.createElement('div', { className: 'card-grid' },
                        accounts.map((acc, i) => React.createElement('div', { key: i, className: 'card' },
                            React.createElement('div', { className: 'card-title' }, 
                                React.createElement('span', { className: 'mr-2' }, 
                                    platforms.find(p => p.id === acc.platform)?.icon || '📱'
                                ),
                                acc.platform.charAt(0).toUpperCase() + acc.platform.slice(1)
                            ),
                            React.createElement('div', { className: 'card-value text-lg' }, acc.account_name),
                            React.createElement('div', { className: 'card-label' }, 'Connected'),
                            React.createElement('button', {
                                onClick: () => handleDisconnectAccount(acc.id),
                                className: 'btn-secondary mt-4 w-full text-sm hover:bg-red-600'
                            }, 'Disconnect')
                        ))
                    ) : React.createElement('div', { className: 'card p-6 text-center' },
                        React.createElement('p', { className: 'text-gray-400 mb-4' }, 'No accounts connected yet'),
                        React.createElement('button', {
                            onClick: () => setShowConnectModal(true),
                            className: 'gradient-btn'
                        }, 'Connect Your First Account')
                    )
                ),

                activeTab === 'hashtags' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, '#️⃣ Hashtag Analysis'),
                    hashtagData ? React.createElement('div', { className: 'space-y-4' },
                        React.createElement('h3', { className: 'text-lg font-bold text-cyan-400' }, 'Top Performing Hashtags'),
                        hashtagData.top_hashtags?.slice(0, 5).map((tag, i) => React.createElement('div', { key: i, className: 'card p-4' },
                            React.createElement('div', { className: 'flex justify-between items-center' },
                                React.createElement('div', {},
                                    React.createElement('div', { className: 'font-bold text-cyan-400' }, tag.tag),
                                    React.createElement('div', { className: 'text-sm text-gray-400' }, `${tag.uses} uses • ${tag.total_engagement} total engagement`)
                                ),
                                React.createElement('span', { className: `px-3 py-1 rounded text-sm font-bold ${tag.performance === 'excellent' ? 'bg-green-500' : tag.performance === 'good' ? 'bg-blue-500' : 'bg-gray-500'}` }, tag.performance)
                            )
                        )),
                        React.createElement('h3', { className: 'text-lg font-bold text-cyan-400 mt-6' }, 'Recommended Hashtags'),
                        hashtagData.recommendations?.map((rec, i) => React.createElement('div', { key: i, className: 'card p-3' },
                            React.createElement('span', { className: 'text-cyan-400 font-bold' }, rec.tag + ' • '),
                            React.createElement('span', { className: 'text-gray-300' }, rec.reason)
                        ))
                    ) : React.createElement('div', { className: 'text-center text-gray-400' }, 'Loading hashtag data...')
                ),

                activeTab === 'audience' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, '👥 Audience Insights'),
                    audienceData ? React.createElement('div', { className: 'space-y-4' },
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-2' }, '📊 Demographics'),
                            React.createElement('div', { className: 'text-sm text-gray-300' },
                                React.createElement('div', {}, '🎂 Age: ' + audienceData.demographics.primary_age),
                                React.createElement('div', {}, '🌍 Top Locations: ' + audienceData.demographics.top_locations.join(', ')),
                                React.createElement('div', {}, '⭐ Interests: ' + audienceData.demographics.interests.join(', '))
                            )
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-2' }, '📈 Behavior Patterns'),
                            React.createElement('div', { className: 'text-sm text-gray-300' },
                                React.createElement('div', {}, '📅 Most Active: ' + audienceData.behavior_patterns.most_active_day),
                                React.createElement('div', {}, '⏰ Peak Time: ' + audienceData.behavior_patterns.peak_engagement_time),
                                React.createElement('div', {}, '📊 Growth: ' + audienceData.behavior_patterns.follower_growth_rate)
                            )
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-2' }, '😊 Sentiment Analysis'),
                            React.createElement('div', { className: 'flex gap-4' },
                                React.createElement('div', {},
                                    React.createElement('div', { className: 'text-2xl font-bold text-green-400' }, audienceData.audience_sentiment.positive + '%'),
                                    React.createElement('div', { className: 'text-xs text-gray-400' }, 'Positive')
                                ),
                                React.createElement('div', {},
                                    React.createElement('div', { className: 'text-2xl font-bold text-yellow-400' }, audienceData.audience_sentiment.neutral + '%'),
                                    React.createElement('div', { className: 'text-xs text-gray-400' }, 'Neutral')
                                ),
                                React.createElement('div', {},
                                    React.createElement('div', { className: 'text-2xl font-bold text-red-400' }, audienceData.audience_sentiment.negative + '%'),
                                    React.createElement('div', { className: 'text-xs text-gray-400' }, 'Negative')
                                )
                            )
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, '❤️ Content Preferences'),
                            audienceData.content_preferences.map((pref, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-1' }, '✓ ' + pref))
                        )
                    ) : React.createElement('div', { className: 'text-center text-gray-400' }, 'Loading audience data...')
                ),

                activeTab === 'competitor' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, '⚔️ Competitor Analysis'),
                    competitorData ? React.createElement('div', { className: 'space-y-4' },
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, '📊 Your Performance'),
                            React.createElement('div', { className: 'grid grid-cols-2 gap-3 text-sm' },
                                React.createElement('div', {}, 
                                    React.createElement('div', { className: 'text-gray-400' }, 'Avg Engagement'),
                                    React.createElement('div', { className: 'text-lg font-bold text-cyan-400' }, competitorData.your_metrics.avg_engagement)
                                ),
                                React.createElement('div', {},
                                    React.createElement('div', { className: 'text-gray-400' }, 'Posting Frequency'),
                                    React.createElement('div', { className: 'text-lg font-bold text-cyan-400' }, competitorData.your_metrics.content_frequency)
                                )
                            )
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, '🎯 vs Industry Benchmark'),
                            competitorData.growth_opportunities?.slice(0, 5).map((opp, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-1 border-b border-gray-700' }, '💡 ' + opp))
                        )
                    ) : React.createElement('div', { className: 'text-center text-gray-400' }, 'Loading competitor analysis...')
                ),

                activeTab === 'predict' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, '🎯 Engagement Predictor'),
                    React.createElement('div', { className: 'card p-6' },
                        React.createElement('label', { className: 'block text-sm font-semibold mb-2 text-gray-300' }, 'Enter your content:'),
                        React.createElement('textarea', {
                            value: predictionContent,
                            onChange: (e) => setPredictionContent(e.target.value),
                            placeholder: 'Paste your post content here to get AI predictions...',
                            rows: 4,
                            className: 'w-full bg-gray-700 border border-gray-600 rounded px-4 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400 mb-4'
                        }),
                        React.createElement('button', {
                            onClick: handlePredictEngagement,
                            className: 'gradient-btn'
                        }, '🔮 Predict Engagement')
                    ),
                    engagementPrediction && React.createElement('div', { className: 'mt-6 space-y-4' },
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'text-lg font-bold text-cyan-400' }, '📊 Prediction Result'),
                            React.createElement('div', { className: 'text-3xl font-bold text-green-400 my-2' }, engagementPrediction.predicted_engagement + ' engagements'),
                            React.createElement('div', { className: 'text-sm text-gray-300' }, 'Confidence: ' + (engagementPrediction.confidence_score * 100) + '%'),
                            React.createElement('div', { className: 'text-sm text-cyan-300 mt-2' }, engagementPrediction.ai_recommendation)
                        ),
                        engagementPrediction.factors?.length > 0 && React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, '✨ Positive Factors'),
                            engagementPrediction.factors.map((f, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-1' },
                                React.createElement('span', { className: 'text-green-400' }, f.factor + ' ' + f.impact),
                                ' - ' + f.tip
                            ))
                        )
                    )
                ),

                activeTab === 'anomalies' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, '⚡ Performance Anomalies'),
                    anomalies ? React.createElement('div', { className: 'space-y-4' },
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400' }, 'Trend: ' + anomalies.trend),
                            React.createElement('div', { className: 'text-sm text-gray-300 mt-2' }, 'Avg Engagement: ' + anomalies.average_engagement)
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, 'Detected Anomalies (' + anomalies.anomalies_detected + ')'),
                            anomalies.anomalies?.slice(0, 5).map((a, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-2 border-b border-gray-700' },
                                React.createElement('span', { className: 'font-bold text-yellow-400' }, a.type + ' - '),
                                React.createElement('span', { className: 'text-gray-400' }, a.analysis)
                            ))
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-2' }, '📈 Key Insights'),
                            anomalies.insights?.map((i, idx) => React.createElement('div', { key: idx, className: 'text-sm text-gray-300 py-1' }, '💡 ' + i))
                        )
                    ) : React.createElement('div', { className: 'text-center text-gray-400' }, 'Loading anomaly detection...')
                ),

                activeTab === 'forecast' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, '📈 Growth Forecast'),
                    forecast ? React.createElement('div', { className: 'space-y-4' },
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, 'Projected Growth (Next 3 Months)'),
                            forecast.monthly_forecast?.map((m, i) => React.createElement('div', { key: i, className: 'border-b border-gray-700 py-3 text-sm' },
                                React.createElement('div', { className: 'flex justify-between' },
                                    React.createElement('span', { className: 'text-cyan-300' }, 'Month ' + m.month),
                                    React.createElement('span', { className: 'text-green-400' }, m.projected_followers.toLocaleString() + ' followers')
                                ),
                                React.createElement('div', { className: 'text-xs text-gray-400 mt-1' }, 'Engagement Rate: ' + m.projected_engagement_rate + '%')
                            ))
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, '🚀 Growth Drivers'),
                            forecast.growth_drivers?.map((d, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-1' }, '✓ ' + d))
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, '📋 Recommendations'),
                            forecast.recommendations_for_growth?.map((r, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-1' }, '💡 ' + r))
                        )
                    ) : React.createElement('div', { className: 'text-center text-gray-400' }, 'Loading forecast...')
                ),

                activeTab === 'calendar' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, '📅 Content Calendar'),
                    contentCalendar ? React.createElement('div', { className: 'space-y-4' },
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, 'Scheduled Posts'),
                            contentCalendar.scheduled_posts?.slice(0, 3).map((post, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-2 border-b border-gray-700' },
                                React.createElement('div', { className: 'flex justify-between' },
                                    React.createElement('span', { className: 'text-cyan-300' }, post.date + ' @ ' + post.time),
                                    React.createElement('span', { className: 'text-green-400' }, post.status)
                                ),
                                React.createElement('div', { className: 'text-xs text-gray-400 mt-1' }, post.content_type + ' • ' + post.platform)
                            ))
                        ),
                        React.createElement('div', { className: 'card p-4' },
                            React.createElement('h3', { className: 'font-bold text-cyan-400 mb-3' }, '📝 Content Themes'),
                            contentCalendar.content_themes?.map((theme, i) => React.createElement('div', { key: i, className: 'text-sm text-gray-300 py-1' }, '📌 ' + theme))
                        )
                    ) : React.createElement('div', { className: 'text-center text-gray-400' }, 'Loading calendar...')
                ),

                activeTab === 'insights' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, 'Insights'),
                    insights.length > 0 ? React.createElement('div', { className: 'space-y-4' },
                        insights.map((ins, i) => React.createElement('div', { key: i, className: 'card p-4' }, '💡 ' + ins))
                    ) : React.createElement('p', { className: 'text-gray-400' }, 'No insights yet')
                ),

                activeTab === 'recommendations' && React.createElement('div', {},
                    React.createElement('h2', { className: 'text-2xl font-bold mb-6' }, 'Recommendations'),
                    React.createElement('div', { className: 'card p-4 mb-4' },
                        React.createElement('h3', { className: 'font-bold mb-2' }, 'Best Posting Times'),
                        React.createElement('ul', { className: 'list-disc ml-6' },
                            React.createElement('li', {}, 'Weekdays: 6-9 PM'),
                            React.createElement('li', {}, 'Weekends: 10 AM-12 PM')
                        )
                    ),
                    React.createElement('div', { className: 'card p-4' },
                        React.createElement('h3', { className: 'font-bold mb-3' }, 'Engagement Tips'),
                        React.createElement('ul', { className: 'space-y-1' },
                            React.createElement('li', { className: 'text-sm text-gray-300' }, '✓ Use 3-5 relevant hashtags'),
                            React.createElement('li', { className: 'text-sm text-gray-300' }, '✓ Include a call-to-action'),
                            React.createElement('li', { className: 'text-sm text-gray-300' }, '✓ Post consistently 3-5 times/week'),
                            React.createElement('li', { className: 'text-sm text-gray-300' }, '✓ Engage with comments within 1 hour'),
                            React.createElement('li', { className: 'text-sm text-gray-300' }, '✓ Use video (3x more engagement)')
                        )
                    )
                )
            )
        )
    );
};

// ==================== Main App Component ====================
const App = () => {
    const [user, setUser] = React.useState(null);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
            try {
                setUser(JSON.parse(storedUser));
            } catch (error) {
                localStorage.removeItem('user');
                localStorage.removeItem('token');
            }
        }
        setLoading(false);
    }, []);

    const handleAuthSuccess = (userData) => {
        setUser(userData);
    };

    const handleLogout = () => {
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        setUser(null);
    };

    if (loading) {
        return React.createElement('div', { className: 'flex items-center justify-center min-h-screen bg-gray-900' },
            React.createElement('div', { className: 'text-2xl gradient-text font-bold' }, 'Loading...')
        );
    }

    return React.createElement(React.Fragment, {},
        user
            ? React.createElement(Dashboard, { user, onLogout: handleLogout })
            : React.createElement(AuthPage, { onAuthSuccess: handleAuthSuccess })
    );
};

// ==================== Render App ====================
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(React.createElement(App));