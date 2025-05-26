const toggleButton = document.getElementsByClassName('toggle-button')[0]
const navbarLinks = document.getElementsByClassName('navbar-links')[0]

toggleButton.addEventListener('click', () => {
  navbarLinks.classList.toggle('active')
})
function clearPlaceholder() {
  const editor = document.getElementById("editor");
  if (editor.innerText === "Commencez à écrire votre article ici...") {
    editor.innerText = "";
  }
}

function restorePlaceholderIfEmpty() {
  const editor = document.getElementById("editor");
  if (editor.innerText.trim() === "") {
    editor.innerText = "Commencez à écrire votre article ici...";
  }
}

function updateStatus() {
  const editor = document.getElementById("editor");
  let text = editor.innerText;
  if (text === "Commencez à écrire votre article ici...") {
    document.getElementById("word-count").innerText = "0 mot, 0 caractère";
    return;
  }
  const words = text.trim().split(/\s+/).filter(w => w.length > 0);
  const characters = text.replace(/\s/g, '');
  document.getElementById("word-count").innerText =
    `${words.length} mot${words.length > 1 ? 's' : ''}, ${characters.length} caractère${characters.length > 1 ? 's' : ''}`;
  document.getElementById("last-modified").innerText =
    "Dernière modification : " + new Date().toLocaleTimeString();
}
document.addEventListener("DOMContentLoaded", function() {
  const editor = document.getElementById("editor");
  if (editor.innerText.trim() === "") {
    editor.innerText = "Commencez à écrire votre article ici...";
  }
  updateStatus();
});
document.addEventListener('DOMContentLoaded', function() {
  document.body.classList.add('animating');
  setTimeout(function() {
      document.body.classList.remove('animating');
      document.querySelector('.fullscreen-loader').remove();
  }, 3000);
});
function toggleLike(articleId) {
  fetch('/check_auth')
    .then(response => response.json())
    .then(data => {
      if (!data.authenticated) {
        window.location.href = '/login';
        return;
      }
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
      fetch(`/article/${articleId}/like`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
      })
      .then(response => response.json())
      .then(data => {
        const likeBtn = document.querySelector(`.like-btn[onclick="toggleLike(${articleId})"]`);
        const likeCount = likeBtn.querySelector('.like-count');
        const likeText = likeBtn.querySelector('.like-text');
        likeCount.textContent = data.likes;
        likeText.textContent = data.liked ? 'Liked' : 'Like';
        likeBtn.classList.toggle('liked', data.liked);
      })
      .catch(error => console.error('Error:', error));
    });
}
document.getElementById('article-form').addEventListener('submit', function(e) {
  const editorContent = document.getElementById('editor').innerHTML;
  document.getElementById('content').value = editorContent;
});
document.getElementById('article-form').addEventListener('submit', function(e) {
  const editorContent = document.getElementById('editor').innerHTML;
  const cleanContent = DOMPurify.sanitize(editorContent);
  document.getElementById('content').value = cleanContent;
});
document.getElementById('editor').innerHTML = yourSavedHtmlContent;


document.querySelectorAll('.reply-form form').forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const discussionId = form.getAttribute('action').split('/').pop();
        
        try {
            const response = await fetch(`/discussion/${discussionId}/reply`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                location.reload(); // Refresh to show new reply
            } else {
                alert(data.message || 'Error posting reply');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while posting your reply');
        }
    });
});