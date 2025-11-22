// Get inputs and use filter button
document.querySelector(".filter_button").addEventListener("click", () => {
  const start = document.getElementById("startDate").value;
  const end = document.getElementById("endDate").value;
  const timeFilter = document.getElementById("timeFilter").value || "all";
  const seasonFilter = document.getElementById("seasonFilter").value || "all";

  // Fetch from backend API (align with tracks; backend aggregates 5 accounts)
  fetch(`/api/top-albums?start=${start}&end=${end}&time=${timeFilter}&season=${seasonFilter}`)
    .then(result => result.json())
    .then(data => renderAlbums(data))
    .catch(err => console.error(err));
});

// Dynamically load the top albums
function renderAlbums(albums) {
  const list = document.getElementById("albumList");
  list.innerHTML = "";

  if (albums.length === 0) {
    list.innerHTML = `<li style="padding: 60px; text-align: center; color: #666; font-size: 18px;">No albums found with the current filters.</li>`;
    return;
  }

  // Iterate through albums and list them (slice to top 50 if needed)
  albums.slice(0, 50).forEach((album, index) => {
    const li = document.createElement("li");
    li.className = "album";
    li.innerHTML = `
      <span class="rank">${index + 1}</span>
      <div class="album-cover"><img src="${album.cover || 'assets/placeholder_album.jpg'}" alt="${album.title}" /></div>
      <span class="title">${album.title}</span>
      <span class="artist">${album.artist}</span>
      <span class="playcount">${album.plays.toLocaleString()} plays</span>
    `;
    list.appendChild(li);
  });
}

// Initial load (all data)
fetch(`/api/top-albums`)
  .then(result => result.json())
  .then(data => renderAlbums(data))
  .catch(err => console.error(err));