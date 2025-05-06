const toggleButton = document.getElementsByClassName('toggle-button')[0]
const navbarLinks = document.getElementsByClassName('navbar-links')[0]

toggleButton.addEventListener('click', () => {
  navbarLinks.classList.toggle('active')
})
function clearPlaceholder() {
  const editor = document.getElementById("editor");
  if (editor.innerText === "Commencez à écrire votre article ici...") {
    editor.innerText = ""; // Clear the placeholder when focused
  }
}

function restorePlaceholderIfEmpty() {
  const editor = document.getElementById("editor");
  if (editor.innerText.trim() === "") {
    editor.innerText = "Commencez à écrire votre article ici..."; // Restore if empty
  }
}

function updateStatus() {
  const editor = document.getElementById("editor");
  let text = editor.innerText;
  
  // Ignore counting if the text is still the placeholder
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
  // Check if user is logged in
  fetch('/check_auth')
      .then(response => response.json())
      .then(data => {
          if (!data.authenticated) {
              window.location.href = '/login';
              return;
          }
          
          // Proceed with like/unlike
          fetch(`/article/${articleId}/like`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
          })
          .then(response => response.json())
          .then(data => {
              const likeBtn = document.querySelector(`.like-btn[onclick="toggleLike(${articleId})"]`);
              const likeCount = likeBtn.querySelector('.like-count');
              const likeText = likeBtn.querySelector('.like-text');
              
              likeCount.textContent = data.likes;
              likeText.textContent = data.liked ? 'Liked' : 'Like';
              
              // Visual feedback
              likeBtn.classList.toggle('liked', data.liked);
          })
          .catch(error => console.error('Error:', error));
      });
}