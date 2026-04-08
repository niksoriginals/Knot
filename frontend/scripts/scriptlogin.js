document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const btn = document.getElementById('loginBtn');

    // Button loading state
    btn.innerHTML = '<i class="fas fa-circle-notch animate-spin"></i> Authenticating...';
    btn.style.pointerEvents = 'none';

    try {
        // Tumhara backend endpoint
        const response = await fetch('https://api.knot.niksoriginals.in/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            btn.innerHTML = 'Success! Redirecting...';
            btn.classList.replace('from-blue-600', 'from-green-600');
            
            setTimeout(() => {
                window.location.href = '/dashboard.html';
            }, 1000);
        } else {
            throw new Error(data.error || 'Login failed');
        }

    } catch (err) {
        // Error handling
        alert(err.message);
        btn.innerHTML = 'Sign In';
        btn.style.pointerEvents = 'all';
    }
});