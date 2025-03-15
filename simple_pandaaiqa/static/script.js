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
    
    // Initialize role selector
    initRoleSelector();
    
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
 * Initialize file upload for all roles
 */
function initFileUpload() {
    console.log('Initializing file uploads for all roles');
    
    // Define all file upload elements by role - CORRECTED ROLE IDENTIFIERS
    const fileUploads = {
        'default': {
            container: document.getElementById('file-upload'),
            input: document.getElementById('file-input'),
            message: document.getElementById('upload-message')
        },
        'customer-support': { // Changed from 'support' to 'customer-support'
            container: document.getElementById('support-file-upload'),
            input: document.getElementById('support-file-input'),
            message: document.getElementById('support-upload-message')
        },
        'sales': {
            container: document.getElementById('sales-file-upload'),
            input: document.getElementById('sales-file-input'),
            message: document.getElementById('sales-upload-message')
        },
        'technical': {
            container: document.getElementById('technical-file-upload'),
            input: document.getElementById('technical-file-input'),
            message: document.getElementById('technical-upload-message')
        }
    };
    
    // Setup each file upload component
    Object.entries(fileUploads).forEach(([role, elements]) => {
        const { container, input, message } = elements;
        
        if (!container || !input) {
            console.warn(`Missing file upload elements for role: ${role}`);
            return;
        }
        
        console.log(`Setting up file upload for role: ${role}`);
        
        // Click to select file
        container.addEventListener('click', (e) => {
            console.log(`File upload container clicked for role: ${role}`);
            // Only trigger click if the click wasn't on the input itself (prevent loop)
            if (e.target !== input) {
                input.click();
            }
        });
        
        // Drag and drop
        container.addEventListener('dragover', (e) => {
            e.preventDefault();
            container.style.backgroundColor = 'rgba(67, 97, 238, 0.1)';
        });
        
        container.addEventListener('dragleave', () => {
            container.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
        });
        
        container.addEventListener('drop', (e) => {
            e.preventDefault();
            container.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
            console.log(`File dropped for role: ${role}`);
            if (e.dataTransfer.files.length) {
                handleFileUpload(e.dataTransfer.files[0], role, message);
            }
        });
        
        // File input change
        input.addEventListener('change', () => {
            console.log(`File input changed for role: ${role}`);
            if (input.files.length) {
                handleFileUpload(input.files[0], role, message);
            }
        });
    });
    
    console.log('File upload initialization complete');
}

/**
 * Handle file upload with role context
 */
function handleFileUpload(file, role, messageElement) {
    console.log(`Handling file upload for role: ${role}, file: ${file.name}`);
    
    const formData = new FormData();
    formData.append('file', file);
    
    // Add role information if it's not the default role
    if (role && role !== 'default') {
        formData.append('role', role);
    }
    
    // Show upload status
    if (messageElement) {
        showMessage(messageElement, `Uploading ${file.name}...`, 'info');
    } else {
        showNotification(`Uploading ${file.name}...`, 'info', 'file-upload');
    }
    
    // Use the existing API endpoint
    const apiUrl = `${API_BASE_URL}/api/upload`;
    
    fetch(apiUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            if (messageElement) {
                showMessage(messageElement, data.message, 'success');
            } else {
                showNotification(data.message, 'success');
                removeNotification('file-upload');
            }
            
            // Update document count
            fetchStatus();
        } else {
            const errorMsg = data.detail || 'Upload failed';
            if (messageElement) {
                showMessage(messageElement, errorMsg, 'error');
            } else {
                showNotification(errorMsg, 'error');
                removeNotification('file-upload');
            }
        }
    })
    .catch(error => {
        console.error('Error uploading file:', error);
        const errorMsg = `Upload error: ${error.message}`;
        
        if (messageElement) {
            showMessage(messageElement, errorMsg, 'error');
        } else {
            showNotification(errorMsg, 'error');
            removeNotification('file-upload');
        }
    });
    
    // Reset file input - FIXED FOR ROLE-SPECIFIC IDs
    let inputId;
    
    // Map role to the correct input ID
    if (role === 'default') {
        inputId = 'file-input';
    } else if (role === 'customer-support') {
        inputId = 'support-file-input';
    } else if (role === 'sales') {
        inputId = 'sales-file-input';
    } else if (role === 'technical') {
        inputId = 'technical-file-input';
    }
    
    const fileInput = document.getElementById(inputId);
    if (fileInput) {
        fileInput.value = '';
        console.log(`Reset file input: ${inputId}`);
    } else {
        console.warn(`Could not find file input with ID: ${inputId}`);
    }
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

/**
 * Initialize role selector
 */
function initRoleSelector() {
    const roleSelectorButton = document.getElementById('role-selector-button');
    const roleDropdown = document.getElementById('role-dropdown');
    const roleOptions = document.querySelectorAll('.role-option');
    const currentRoleText = document.getElementById('current-role');
    const roleContents = document.querySelectorAll('.role-content');
    
    if (!roleSelectorButton || !roleDropdown) return;
    
    // Toggle dropdown
    roleSelectorButton.addEventListener('click', () => {
        roleDropdown.classList.toggle('active');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (event) => {
        if (!roleSelectorButton.contains(event.target) && !roleDropdown.contains(event.target)) {
            roleDropdown.classList.remove('active');
        }
    });
    
    // Role selection
    roleOptions.forEach(option => {
        option.addEventListener('click', () => {
            // Update active option styling
            roleOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            
            // Update current role text
            currentRoleText.textContent = option.textContent;
            
            // Hide dropdown
            roleDropdown.classList.remove('active');
            
            // Show appropriate content
            const selectedRole = option.getAttribute('data-role');
            roleContents.forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${selectedRole}-role`).classList.add('active');
            
            // Store the selected role in localStorage for persistence
            localStorage.setItem('selectedRole', selectedRole);
            
            console.log(`Role changed to: ${selectedRole}`);
        });
    });
    
    // Initialize from localStorage if available
    const savedRole = localStorage.getItem('selectedRole');
    if (savedRole) {
        const savedRoleOption = document.querySelector(`.role-option[data-role="${savedRole}"]`);
        if (savedRoleOption) {
            savedRoleOption.click();
        }
    }
    
    // Add role-specific query handlers
    bindRoleSpecificQueryHandlers();
}

/**
 * Bind event handlers for role-specific query forms
 */
function bindRoleSpecificQueryHandlers() {
    const roleQueryButtons = {
        'support': document.getElementById('support-query-button'),
        'sales': document.getElementById('sales-query-button'),
        'technical': document.getElementById('technical-query-button')
    };
    
    const roleQueryInputs = {
        'support': document.getElementById('support-query-input'),
        'sales': document.getElementById('sales-query-input'),
        'technical': document.getElementById('technical-query-input')
    };
    
    // Customer Support query
    if (roleQueryButtons.support) {
        roleQueryButtons.support.addEventListener('click', () => {
            const query = roleQueryInputs.support.value;
            if (query.trim() !== '') {
                handleRoleSpecificQuery(query, 'customer-support');
            }
        });
    }
    
    // Sales query
    if (roleQueryButtons.sales) {
        roleQueryButtons.sales.addEventListener('click', () => {
            const query = roleQueryInputs.sales.value;
            if (query.trim() !== '') {
                handleRoleSpecificQuery(query, 'sales');
            }
        });
    }
    
    // Technical query
    if (roleQueryButtons.technical) {
        roleQueryButtons.technical.addEventListener('click', () => {
            const query = roleQueryInputs.technical.value;
            if (query.trim() !== '') {
                handleRoleSpecificQuery(query, 'technical');
            }
        });
    }
    
    // Add enter key support for all role inputs
    Object.values(roleQueryInputs).forEach((input, index) => {
        if (input) {
            input.addEventListener('keyup', (e) => {
                if (e.key === 'Enter') {
                    const roleTypes = ['customer-support', 'sales', 'technical'];
                    const roleType = roleTypes[index];
                    const query = input.value;
                    if (query.trim() !== '') {
                        handleRoleSpecificQuery(query, roleType);
                    }
                }
            });
        }
    });
}

/**
 * Handle a role-specific query
 */
function handleRoleSpecificQuery(query, roleType) {
    // Show notification about processing
    showNotification(`Processing ${roleType} query...`, 'info', `${roleType}-query`);
    
    // Create a new card to show the answer if it doesn't exist
    let answerCard = document.querySelector(`.${roleType}-answer-card`);
    
    if (!answerCard) {
        answerCard = document.createElement('div');
        answerCard.className = `card ${roleType}-answer-card`;
        answerCard.innerHTML = `
            <h3>Answer</h3>
            <div class="role-answer">Processing your query...</div>
            <h3>Relevant Context</h3>
            <div class="role-context-container"></div>
        `;
        
        // Add the card to the role content
        document.getElementById(`${roleType}-role`).appendChild(answerCard);
    } else {
        // Update existing card
        const answerDiv = answerCard.querySelector('.role-answer');
        answerDiv.textContent = "Processing your query...";
    }
    
    // Add role-specific context to the query
    const contextualizedQuery = getRoleContext(query, roleType);
    
    // Send to your existing query endpoint with role context
    const apiUrl = `${API_BASE_URL}/api/query`;
    
    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: contextualizedQuery,
            top_k: 3,
            role: roleType // Send role information to the server
        }),
    })
    .then(response => response.json())
    .then(data => {
        const answerDiv = answerCard.querySelector('.role-answer');
        answerDiv.textContent = data.answer || getRoleMockResponse(roleType);
        
        // Display context if available
        const contextContainer = answerCard.querySelector('.role-context-container');
        if (contextContainer && data.context && data.context.length > 0) {
            contextContainer.innerHTML = ''; // Clear previous context
            
            data.context.forEach(item => {
                const contextItem = document.createElement('div');
                contextItem.className = 'context-item';
                
                let sourceInfo = '';
                if (item.metadata && item.metadata.source) {
                    sourceInfo = `<div class="context-source">Source: ${item.metadata.source}</div>`;
                }
                
                contextItem.innerHTML = `
                    ${sourceInfo}
                    <div class="context-text">${item.text}</div>
                    <div class="context-score">Relevance: ${(item.score * 100).toFixed(1)}%</div>
                `;
                
                contextContainer.appendChild(contextItem);
            });
        } else if (contextContainer) {
            contextContainer.innerHTML = '<p>No relevant context found</p>';
        }
        
        removeNotification(`${roleType}-query`);
    })
    .catch(error => {
        console.error('Error in role query:', error);
        
        // Fall back to mock response in case of error
        const answerDiv = answerCard.querySelector('.role-answer');
        answerDiv.textContent = getRoleMockResponse(roleType);
        
        removeNotification(`${roleType}-query`);
        showNotification('Error processing query, showing sample response', 'warning');
    });
}

/**
 * Add role-specific context to a query
 */
function getRoleContext(query, roleType) {
    const contextPrefix = {
        'customer-support': 'As a customer support agent, answer this question: ',
        'sales': 'As a sales representative, address this inquiry: ',
        'technical': 'As a technical specialist, provide information on: '
    };
    
    return `${contextPrefix[roleType] || ''}${query}`;
}

/**
 * Get a mock response for a specific role (fallback if API fails)
 */
function getRoleMockResponse(roleType) {
    const responses = {
        'customer-support': "Based on our customer support knowledge base, I can help resolve this issue by verifying the customer's account and resetting their credentials. Would you like me to provide the step-by-step guide?",
        'sales': "From our sales perspective, I can tell you that our premium package offers the best value with a 15% discount for annual subscriptions. Would you like to see our detailed pricing comparison?",
        'technical': "From a technical standpoint, this is implemented through our API using the endpoint POST /api/v2/resources with parameters {id: string, config: object}. Let me know if you need a code example."
    };
    
    return responses[roleType] || "I'll need to look into that and get back to you.";
}

/**
 * Show message helper
 */
function showMessage(element, message, type) {
    if (!element) {
        console.warn('Message element not found, showing notification instead');
        showNotification(message, type);
        return;
    }
    
    element.textContent = message;
    element.className = 'message ' + type;
    element.style.display = 'block';

    // Hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
} 