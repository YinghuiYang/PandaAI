/**
 * PandaAIQA Frontend Script
 */

// DOM elements
let systemStatus;
let docCount;
let clearButton;
let tabButtons;
let tabContents;
let textForm;
let textInput;
let textSource;
let fileForm;
let fileInput;
let fileName;
let queryForm;
let queryInput;
let topK;
let answerContainer;
let answer;
let contextContainer;
let context;
let notifications;

// API base URL
const API_BASE_URL = window.location.origin;

/**
 * Initialize after page load
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - starting initialization');
    
    // Initialize DOM elements
    initDomElements();
    
    // Initialize tabs
    initTabs();
    
    // Initialize file upload
    initFileUpload();
    
    // Get system status
    fetchStatus();
    
    // Bind form submissions
    bindFormSubmissions();
    
    // Bind clear button
    bindClearButton();
    
    // Log debugging info
    console.log('Page initialized, API base URL:', API_BASE_URL);
    console.log('DOM Elements loaded:', {
        textForm: !!textForm,
        textInput: !!textInput,
        textSource: !!textSource,
        fileForm: !!fileForm,
        fileInput: !!fileInput
    });
    
    // Debug form elements
    if (textForm) {
        console.log('Text form found with ID:', textForm.id);
        console.log('Text form has these elements:', textForm.elements.length);
        
        // Manually add event listener to submit button
        const submitButton = textForm.querySelector('button[type="submit"]');
        if (submitButton) {
            console.log('Submit button found in text form');
            submitButton.addEventListener('click', function(e) {
                console.log('Submit button clicked directly');
            });
        } else {
            console.error('Submit button NOT found in text form');
        }
    } else {
        console.error('Text form element not found by ID');
        // Try to find it by alternate means
        const possibleForm = document.querySelector('form');
        if (possibleForm) {
            console.log('Found a form element by tag:', possibleForm);
        }
    }
});

/**
 * Initialize DOM elements
 */
function initDomElements() {
    console.log('Initializing DOM elements');
    systemStatus = document.getElementById('system-status');
    docCount = document.getElementById('doc-count');
    clearButton = document.getElementById('clear-button');
    tabButtons = document.querySelectorAll('.tab-button');
    tabContents = document.querySelectorAll('.tab-content');
    textForm = document.getElementById('text-form');
    textInput = document.getElementById('text-input');
    textSource = document.getElementById('text-source');
    fileForm = document.getElementById('file-form');
    fileInput = document.getElementById('file-input');
    fileName = document.getElementById('file-name');
    queryForm = document.getElementById('query-form');
    queryInput = document.getElementById('query-input');
    topK = document.getElementById('top-k');
    answerContainer = document.getElementById('answer-container');
    answer = document.getElementById('answer');
    contextContainer = document.getElementById('context-container');
    context = document.getElementById('context');
    notifications = document.getElementById('notifications');
}

/**
 * Initialize tab switching
 */
function initTabs() {
    if (!tabButtons) return;
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove all active states
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add current active state
            button.classList.add('active');
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

/**
 * Initialize file upload
 */
function initFileUpload() {
    if (!fileInput || !fileName) return;
    
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            fileName.textContent = fileInput.files[0].name;
        } else {
            fileName.textContent = 'No file selected';
        }
    });
}

/**
 * Get system status
 */
async function fetchStatus() {
    try {
        console.log('Fetching system status from:', `${API_BASE_URL}/api/status`);
        const response = await fetch(`${API_BASE_URL}/api/status`);
        const data = await response.json();
        
        if (systemStatus) systemStatus.textContent = data.status === 'ready' ? 'Running' : 'Stopped';
        if (docCount) docCount.textContent = data.document_count || 0;
        console.log('Status data received:', data);
    } catch (error) {
        console.error('Failed to get system status:', error);
        if (systemStatus) systemStatus.textContent = 'Error';
        showNotification('Unable to connect to server, please check your network connection', 'error');
    }
}

/**
 * Bind form submission events
 */
function bindFormSubmissions() {
    console.log('Binding form submissions');
    
    // Add text form
    if (textForm) {
        console.log('Adding event listener to text form');
        
        // First try with normal event listener
        textForm.addEventListener('submit', async (e) => {
            console.log('Text form submit event triggered');
            e.preventDefault();
            
            if (!textInput) {
                console.error('Text input element not found');
                showNotification('Error: Text input element not found', 'error');
                return;
            }
            
            const text = textInput.value ? textInput.value.trim() : '';
            if (!text) {
                showNotification('Please enter text content', 'warning');
                return;
            }
            
            const source = textSource && textSource.value ? textSource.value.trim() : '';
            let metadata = {};
            
            if (source) {
                metadata.source = source;
            }
            
            try {
                showNotification('Processing...', 'info', 'processing');
                
                // Debug - log the request payload
                console.log('Sending text processing request:', {
                    text,
                    metadata
                });
                
                const apiUrl = `${API_BASE_URL}/api/process`;
                console.log('API URL:', apiUrl);
                
                console.log('About to send fetch request to:', apiUrl);
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text,
                        metadata
                    }),
                });
                
                // Debug - log the response status
                console.log('Response status:', response.status);
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if (response.ok) {
                    showNotification(data.message, 'success');
                    if (textInput) textInput.value = '';
                    if (textSource) textSource.value = '';
                    fetchStatus();
                } else {
                    showNotification(data.message || 'Failed to process text', 'error');
                }
            } catch (error) {
                console.error('Error adding text:', error);
                console.error('Error details:', error.message, error.stack);
                showNotification(`Error adding text: ${error.message}`, 'error');
            } finally {
                removeNotification('processing');
            }
        });
        
        // Also add manual event handler for button click
        const submitBtn = textForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.addEventListener('click', function(e) {
                console.log('Submit button clicked, form will be submitted');
            });
        }
    } else {
        console.error('Text form element not found');
    }
    
    // Upload file form
    if (fileForm) {
        console.log('Adding event listener to file form');
        fileForm.addEventListener('submit', async (e) => {
            console.log('File form submit event triggered');
            e.preventDefault();
            
            if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
                showNotification('Please select a file', 'warning');
                return;
            }
            
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                showNotification('Uploading...', 'info', 'uploading');
                
                // Debug - log the file being uploaded
                console.log('Uploading file:', file.name);
                
                const apiUrl = `${API_BASE_URL}/api/upload`;
                console.log('API URL:', apiUrl);
                
                console.log('About to send fetch request to:', apiUrl);
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    body: formData,
                });
                
                // Debug - log the response status
                console.log('Response status:', response.status);
                
                const data = await response.json();
                console.log('Response data:', data);
                
                if (response.ok) {
                    showNotification(data.message, 'success');
                    if (fileInput) fileInput.value = '';
                    if (fileName) fileName.textContent = 'No file selected';
                    fetchStatus();
                } else {
                    showNotification(data.message || 'Failed to upload file', 'error');
                }
            } catch (error) {
                console.error('Error uploading file:', error);
                console.error('Error details:', error.message, error.stack);
                showNotification(`Error uploading file: ${error.message}`, 'error');
            } finally {
                removeNotification('uploading');
            }
        });
    }
    
    // Query form
    if (queryForm) {
        console.log('Adding event listener to query form');
        queryForm.addEventListener('submit', async (e) => {
            console.log('Query form submit event triggered');
            e.preventDefault();
            
            if (!queryInput) {
                showNotification('Query input element not found', 'error');
                return;
            }
            
            const text = queryInput.value ? queryInput.value.trim() : '';
            if (!text) {
                showNotification('Please enter a query', 'warning');
                return;
            }
            
            const k = topK && parseInt(topK.value) ? parseInt(topK.value) : 3;
            
            try {
                showNotification('Querying...', 'info', 'querying');
                
                // Hide previous results
                if (answerContainer) answerContainer.classList.add('hidden');
                if (contextContainer) contextContainer.classList.add('hidden');
                
                const apiUrl = `${API_BASE_URL}/api/query`;
                console.log('API URL:', apiUrl);
                
                console.log('About to send fetch request to:', apiUrl);
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text,
                        top_k: k
                    }),
                });
                
                const data = await response.json();
                console.log('Query response:', data);
                
                if (response.ok) {
                    // Show results
                    if (answer && answerContainer) {
                        answer.textContent = data.answer;
                        answerContainer.classList.remove('hidden');
                    }
                    
                    // Show context
                    if (context && contextContainer) {
                        context.innerHTML = '';
                        if (data.context && data.context.length > 0) {
                            renderContext(data.context);
                            contextContainer.classList.remove('hidden');
                        }
                    }
                } else {
                    showNotification(data.message || 'Query failed', 'error');
                }
            } catch (error) {
                console.error('Error during query:', error);
                console.error('Error details:', error.message, error.stack);
                showNotification(`Error during query: ${error.message}`, 'error');
            } finally {
                removeNotification('querying');
            }
        });
    }
}

/**
 * Bind clear button event
 */
function bindClearButton() {
    if (!clearButton) return;
    
    clearButton.addEventListener('click', async () => {
        if (confirm('Are you sure you want to clear the knowledge base? This action cannot be undone.')) {
            try {
                const apiUrl = `${API_BASE_URL}/api/clear`;
                console.log('API URL:', apiUrl);
                
                const response = await fetch(apiUrl, {
                    method: 'DELETE',
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showNotification(data.message, 'success');
                    fetchStatus();
                    
                    // Clear results area
                    if (answerContainer) answerContainer.classList.add('hidden');
                    if (contextContainer) contextContainer.classList.add('hidden');
                } else {
                    showNotification(data.message || 'Failed to clear knowledge base', 'error');
                }
            } catch (error) {
                console.error('Error clearing knowledge base:', error);
                showNotification('Error clearing knowledge base', 'error');
            }
        }
    });
}

/**
 * Render context results
 */
function renderContext(contextData) {
    if (!context) return;
    
    context.innerHTML = '';
    
    contextData.forEach((item, index) => {
        const contextItem = document.createElement('div');
        contextItem.className = 'context-item';
        
        // Add similarity score
        const scoreElem = document.createElement('div');
        scoreElem.className = 'score';
        scoreElem.textContent = `Similarity: ${(item.score * 100).toFixed(2)}%`;
        contextItem.appendChild(scoreElem);
        
        // Add text content
        const textElem = document.createElement('div');
        textElem.textContent = item.text;
        contextItem.appendChild(textElem);
        
        // Add metadata (if any)
        if (item.metadata && Object.keys(item.metadata).length > 0) {
            const metaElem = document.createElement('div');
            metaElem.className = 'metadata';
            metaElem.style.marginTop = '0.5rem';
            metaElem.style.fontSize = '0.85rem';
            metaElem.style.color = 'var(--secondary-color)';
            
            let metaText = '';
            if (item.metadata.source) {
                metaText += `Source: ${item.metadata.source}`;
            }
            
            metaElem.textContent = metaText;
            contextItem.appendChild(metaElem);
        }
        
        context.appendChild(contextItem);
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info', id = null) {
    if (!notifications) {
        console.error('Notifications element not found');
        console.log(message, type);
        return;
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    if (id) {
        notification.id = `notification-${id}`;
        // Check if notification with same ID already exists
        const existing = document.getElementById(`notification-${id}`);
        if (existing) {
            existing.textContent = message;
            return;
        }
    }
    
    notifications.appendChild(notification);
    
    // Auto-dismiss if not persistent
    if (!id) {
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                if (notification.parentNode === notifications) {
                    notifications.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

/**
 * Remove notification by ID
 */
function removeNotification(id) {
    const notification = document.getElementById(`notification-${id}`);
    if (notification) {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        
        setTimeout(() => {
            if (notification.parentNode === notifications) {
                notifications.removeChild(notification);
            }
        }, 300);
    }
} 