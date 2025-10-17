class OkkoAIAssistant {
    constructor() {
        this.apiBaseUrl = 'http://localhost:5000/api';
        this.sessionId = this.generateSessionId();
        this.messageHistory = [];
        this.currentContext = {
            time: this.getCurrentTime(),
            weather: 'Солнечно, +15°C',
            location: 'Москва',
            mood: 'neutral'
        };
        
        this.initializeElements();
        this.bindEvents();
        this.updateContext();
        this.loadSession();
        
        // Auto-resize textarea
        this.autoResizeTextarea();
    }

    generateSessionId() {
        return 'okko_session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initializeElements() {
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.recommendationsContainer = document.getElementById('recommendationsContainer');
        
        // Context elements
        this.contextDisplay = document.getElementById('contextDisplay');
        this.timeContext = document.getElementById('timeContext');
        this.moodContext = document.getElementById('moodContext');
        this.weatherContext = document.getElementById('weatherContext');
        
        // Sidebar elements
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.sidebarTime = document.getElementById('sidebarTime');
        this.sidebarLocation = document.getElementById('sidebarLocation');
        this.sidebarWeather = document.getElementById('sidebarWeather');
        
        // Examples dropdown
        this.examplesBtn = document.getElementById('examplesBtn');
        this.examplesList = document.getElementById('examplesList');
        
        // Quick filters
        this.filterBtns = document.querySelectorAll('.filter-btn');
    }

    bindEvents() {
        // Send message events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Input events
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButton();
        });

        // Sidebar toggle
        this.sidebarToggle.addEventListener('click', () => {
            this.sidebar.classList.toggle('open');
        });

        // Examples dropdown
        this.examplesBtn.addEventListener('click', () => {
            this.examplesList.classList.toggle('show');
        });

        // Example items
        document.querySelectorAll('.example-item').forEach(item => {
            item.addEventListener('click', () => {
                const example = item.dataset.example;
                this.messageInput.value = example;
                this.autoResizeTextarea();
                this.updateSendButton();
                this.examplesList.classList.remove('show');
                this.messageInput.focus();
            });
        });

        // Quick filters
        this.filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const mood = btn.dataset.mood;
                this.setMood(mood);
                btn.classList.toggle('active');
                
                // Remove active from other buttons
                this.filterBtns.forEach(otherBtn => {
                    if (otherBtn !== btn) {
                        otherBtn.classList.remove('active');
                    }
                });
            });
        });

        // Click outside to close dropdowns
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.examples-dropdown')) {
                this.examplesList.classList.remove('show');
            }
            if (!e.target.closest('.sidebar') && window.innerWidth <= 768) {
                this.sidebar.classList.remove('open');
            }
        });

        // Detect user location
        this.detectLocation();
    }

    getCurrentTime() {
        const now = new Date();
        const hours = now.getHours();
        const day = now.toLocaleDateString('ru-RU', { weekday: 'long' });
        
        let timeOfDay;
        if (hours >= 6 && hours < 12) timeOfDay = 'Утро';
        else if (hours >= 12 && hours < 18) timeOfDay = 'День';
        else if (hours >= 18 && hours < 22) timeOfDay = 'Вечер';
        else timeOfDay = 'Ночь';
        
        return {
            hour: hours,
            day: day,
            timeOfDay: timeOfDay,
            formatted: `${hours}:${now.getMinutes().toString().padStart(2, '0')}, ${day}`
        };
    }

    updateContext() {
        const time = this.getCurrentTime();
        const timeIcon = this.getTimeIcon(time.hour);
        
        this.timeContext.textContent = `${timeIcon} ${time.timeOfDay}`;
        this.sidebarTime.textContent = time.formatted;
        this.sidebarLocation.textContent = this.currentContext.location;
        this.sidebarWeather.textContent = this.currentContext.weather;
        
        this.updateMoodDisplay();
    }

    getTimeIcon(hour) {
        if (hour >= 6 && hour < 12) return '??';
        if (hour >= 12 && hour < 18) return '??';
        if (hour >= 18 && hour < 22) return '??';
        return '??';
    }

    updateMoodDisplay() {
        const moodEmojis = {
            happy: '?? Хорошее настроение',
            sad: '?? Грустное настроение',
            excited: '?? Возбужденное',
            relaxed: '?? Спокойное',
            romantic: '?? Романтическое',
            thoughtful: '?? Задумчивое',
            scared: '?? Страшно',
            energetic: '? Энергичное',
            neutral: '?? Нейтральное'
        };
        
        this.moodContext.textContent = moodEmojis[this.currentContext.mood] || moodEmojis.neutral;
    }

    setMood(mood) {
        this.currentContext.mood = mood;
        this.updateMoodDisplay();
    }

    detectLocation() {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    // In a real app, you would geocode these coordinates
                    // For demo purposes, we'll keep the default location
                    console.log('Location detected:', position.coords.latitude, position.coords.longitude);
                },
                (error) => {
                    console.log('Location detection failed:', error.message);
                }
            );
        }
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    updateSendButton() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText;
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input and update UI
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateSendButton();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to backend API
            const response = await this.callAPI(message);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add assistant response
            this.addMessage(response.message, 'assistant');
            
            // Display recommendations if any
            if (response.recommendations && response.recommendations.length > 0) {
                this.displayRecommendations(response.recommendations);
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            
            // Show fallback response with mock recommendations
            this.handleFallbackResponse(message);
        }
        
        // Save session
        this.saveSession();
    }

    async callAPI(message) {
        const payload = {
            message: message,
            session_id: this.sessionId,
            context: this.currentContext,
            history: this.messageHistory.slice(-10) // Last 10 messages
        };

        const response = await fetch(`${this.apiBaseUrl}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }

    handleFallbackResponse(userMessage) {
        // Generate contextual response based on user message
        let assistantMessage = 'Понимаю! ';
        const lowerMessage = userMessage.toLowerCase();
        
        if (lowerMessage.includes('комед') || lowerMessage.includes('весел') || lowerMessage.includes('смеш')) {
            assistantMessage += 'Вы хотите что-то веселое! Вот несколько отличных комедий:';
            this.displayMockRecommendations('comedy');
        } else if (lowerMessage.includes('драм') || lowerMessage.includes('серьез') || lowerMessage.includes('грустн')) {
            assistantMessage += 'Настроены на что-то серьезное? Рекомендую эти драмы:';
            this.displayMockRecommendations('drama');
        } else if (lowerMessage.includes('романт') || lowerMessage.includes('любов')) {
            assistantMessage += 'Романтическое настроение! Вот прекрасные фильмы о любви:';
            this.displayMockRecommendations('romance');
        } else if (lowerMessage.includes('ужас') || lowerMessage.includes('страшн') || lowerMessage.includes('хоррор')) {
            assistantMessage += 'Хотите пощекотать нервы? Эти фильмы ужасов точно подойдут:';
            this.displayMockRecommendations('horror');
        } else if (lowerMessage.includes('боевик') || lowerMessage.includes('экшн') || lowerMessage.includes('действи')) {
            assistantMessage += 'Любите экшн? Вот захватывающие боевики:';
            this.displayMockRecommendations('action');
        } else {
            assistantMessage += 'Основываясь на вашем запросе и текущем времени, рекомендую:';
            this.displayMockRecommendations('mixed');
        }
        
        this.addMessage(assistantMessage, 'assistant');
    }

    displayMockRecommendations(genre) {
        const mockData = {
            comedy: [
                {
                    title: 'Отпетые мошенники',
                    genres: ['Комедия', 'Приключения'],
                    description: 'Два мошенника соревнуются в искусстве обмана богатых туристов на французской Ривьере.',
                    score: 8.2,
                    url: 'https://okko.tv/movie/comedy1'
                },
                {
                    title: 'Невероятная жизнь Уолтера Митти',
                    genres: ['Комедия', 'Драма', 'Приключения'],
                    description: 'Скромный сотрудник журнала отправляется в невероятное путешествие вокруг света.',
                    score: 7.8,
                    url: 'https://okko.tv/movie/comedy2'
                }
            ],
            drama: [
                {
                    title: 'Форма воды',
                    genres: ['Драма', 'Фэнтези', 'Романтика'],
                    description: 'История любви между немой уборщицей и загадочным амфибией-гуманоидом.',
                    score: 9.1,
                    url: 'https://okko.tv/movie/drama1'
                },
                {
                    title: 'Три билборда на границе Эббинга, Миссури',
                    genres: ['Драма', 'Криминал'],
                    description: 'Мать, потерявшая дочь, бросает вызов местной полиции, арендовав три билборда.',
                    score: 8.9,
                    url: 'https://okko.tv/movie/drama2'
                }
            ],
            romance: [
                {
                    title: 'Ла-Ла Ленд',
                    genres: ['Мюзикл', 'Романтика', 'Драма'],
                    description: 'История любви между джазовым пианистом и начинающей актрисой в Лос-Анджелесе.',
                    score: 8.7,
                    url: 'https://okko.tv/movie/romance1'
                },
                {
                    title: 'Вечное сияние чистого разума',
                    genres: ['Романтика', 'Драма', 'Фантастика'],
                    description: 'Мужчина пытается стереть воспоминания о бывшей девушке из своей памяти.',
                    score: 8.5,
                    url: 'https://okko.tv/movie/romance2'
                }
            ],
            horror: [
                {
                    title: 'Наследственное',
                    genres: ['Ужасы', 'Триллер', 'Драма'],
                    description: 'После смерти матери семью начинают преследовать ужасающие тайны.',
                    score: 7.9,
                    url: 'https://okko.tv/movie/horror1'
                },
                {
                    title: 'Тихое место',
                    genres: ['Ужасы', 'Триллер', 'Фантастика'],
                    description: 'Семья живет в полной тишине, скрываясь от существ, охотящихся по звуку.',
                    score: 8.1,
                    url: 'https://okko.tv/movie/horror2'
                }
            ],
            action: [
                {
                    title: 'Джон Уик',
                    genres: ['Боевик', 'Триллер'],
                    description: 'Бывший киллер выходит из отставки, чтобы отомстить за убийство своей собаки.',
                    score: 8.4,
                    url: 'https://okko.tv/movie/action1'
                },
                {
                    title: 'Безумный Макс: Дорога ярости',
                    genres: ['Боевик', 'Фантастика', 'Приключения'],
                    description: 'В пост-апокалиптическом мире Макс помогает группе женщин сбежать от тирана.',
                    score: 8.8,
                    url: 'https://okko.tv/movie/action2'
                }
            ],
            mixed: [
                {
                    title: 'Паразиты',
                    genres: ['Триллер', 'Драма', 'Комедия'],
                    description: 'Бедная семья постепенно проникает в жизнь богатой семьи с непредсказуемыми последствиями.',
                    score: 9.3,
                    url: 'https://okko.tv/movie/mixed1'
                },
                {
                    title: 'Интерстеллар',
                    genres: ['Фантастика', 'Драма', 'Приключения'],
                    description: 'Группа астронавтов путешествует через червоточину в поисках нового дома для человечества.',
                    score: 9.0,
                    url: 'https://okko.tv/movie/mixed2'
                },
                {
                    title: 'Джокер',
                    genres: ['Драма', 'Триллер', 'Криминал'],
                    description: 'Происхождение одного из самых известных злодеев в истории комиксов.',
                    score: 8.6,
                    url: 'https://okko.tv/movie/mixed3'
                }
            ]
        };
        
        const recommendations = mockData[genre] || mockData.mixed;
        this.displayRecommendations(recommendations);
    }

    displayRecommendations(recommendations) {
        const grid = document.createElement('div');
        grid.className = 'recommendations-grid';
        
        recommendations.forEach(movie => {
            const card = this.createMovieCard(movie);
            grid.appendChild(card);
        });
        
        this.recommendationsContainer.innerHTML = '';
        this.recommendationsContainer.appendChild(grid);
        
        // Scroll to recommendations
        setTimeout(() => {
            this.recommendationsContainer.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'nearest' 
            });
        }, 100);
    }

    createMovieCard(movie) {
        const card = document.createElement('div');
        card.className = 'movie-card';
        
        const genresHtml = movie.genres.map(genre => 
            `<span class="genre-tag">${genre}</span>`
        ).join('');
        
        card.innerHTML = `
            <div class="movie-card__poster">
                <i class="fas fa-film"></i>
            </div>
            <div class="movie-card__content">
                <h3 class="movie-card__title">${movie.title}</h3>
                <div class="movie-card__genres">${genresHtml}</div>
                <p class="movie-card__description">${movie.description}</p>
                <div class="movie-card__footer">
                    <div class="movie-card__score">${movie.score}</div>
                    <a href="${movie.url}" target="_blank" class="movie-card__btn">
                        <i class="fas fa-play"></i>
                        Смотреть на Okko
                    </a>
                </div>
            </div>
        `;
        
        card.style.animation = 'slideIn 0.5s ease-out';
        return card;
    }

    addMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message__avatar';
        avatarDiv.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message__content';
        contentDiv.innerHTML = `<p>${content}</p>`;
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        this.chatMessages.appendChild(messageDiv);
        
        // Store in history
        this.messageHistory.push({
            content: content,
            sender: sender,
            timestamp: new Date().toISOString()
        });
        
        // Scroll to bottom
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }

    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }

    saveSession() {
        const sessionData = {
            sessionId: this.sessionId,
            messageHistory: this.messageHistory,
            context: this.currentContext,
            timestamp: new Date().toISOString()
        };
        
        // Note: localStorage is not available in sandboxed environment
        // In a real implementation, this would save to localStorage or send to server
        console.log('Session saved:', sessionData);
    }

    loadSession() {
        // Note: localStorage is not available in sandboxed environment
        // In a real implementation, this would load from localStorage
        console.log('Session loaded for:', this.sessionId);
        
        // For demo, we'll start fresh each time
        this.messageHistory = [];
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new OkkoAIAssistant();
    
    // Add some demo functionality
    console.log('Okko AI Assistant initialized successfully');
    
    // Update time every minute
    setInterval(() => {
        app.updateContext();
    }, 60000);
});