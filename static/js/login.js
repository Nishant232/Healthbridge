document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    const showSignupLink = document.getElementById('showSignup');
    const showLoginLink = document.getElementById('showLogin');
    const loginCard = document.getElementById('loginForm');
    const signupCard = document.getElementById('signupCard');
    const roleSelect = document.getElementById('role');
    const doctorFields = document.getElementById('doctorFields');
    
    // Toggle between login and signup forms
    showSignupLink.addEventListener('click', function(e) {
        e.preventDefault();
        loginCard.style.display = 'none';
        signupCard.style.display = 'block';
    });
    
    showLoginLink.addEventListener('click', function(e) {
        e.preventDefault();
        signupCard.style.display = 'none';
        loginCard.style.display = 'block';
    });

    // Show/hide additional fields based on role selection
    roleSelect.addEventListener('change', function() {
        if (this.value === 'doctor') {
            doctorFields.style.display = 'block';
        } else {
            doctorFields.style.display = 'none';
        }
    });
    
    // Handle login form submission
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        // Create request data
        const data = {
            email: email,
            password: password
        };
        
        // Send login request
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data && data.success) {
                window.location.href = data.redirect;
            } else if (data && data.message) {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Login failed. Please try again.');
        });
    });

    // Handle signup form submission
    signupForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Collect form data
        const formData = {
            role: document.getElementById('role').value,
            name: document.getElementById('name').value,
            email: document.getElementById('signupEmail').value,
            password: document.getElementById('signupPassword').value
        };
        
        // Add optional doctor fields if role is doctor
        if (formData.role === 'doctor') {
            formData.license = document.getElementById('license').value;
            formData.registrationYear = document.getElementById('registrationYear').value;
        }
        
        // Validate form
        if (!formData.role) {
            alert('Please select an account type');
            return;
        }
        
        // Send signup request
        fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Account created successfully. Please log in.');
                // Switch back to login form
                signupCard.style.display = 'none';
                loginCard.style.display = 'block';
            } else {
                alert(data.message || 'Signup failed. Please try again.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Signup failed. Please try again.');
        });
    });
});