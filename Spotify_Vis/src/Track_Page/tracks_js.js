// Get Date inputs and ouputs and use filter button
document.getElementById("filterButton").addEventListener("click", () => {
    const start = document.getElementById("startDate").value;
    const end   = document.getElementById("endDate").value;

    // Need to edit later to match backend API
    fetch(`/api/top-tracks?start=${start}&end=${end}`)
        .then(result => result.json())
        .then(data => renderTracks(data))
        .catch(err => console.error(err));
});

// Dynamically load the top 10 tracks
function renderTracks(tracks) {
    const list = document.getElementById("songList");
    list.innerHTML = ""; 

    // iterate through tracks and list them
    tracks.forEach((track, index) => {
        const li = document.createElement("li");
        // Located in song-list in html
        li.className = "song";
        li.innerHTML = `
            <span class="rank">${index + 1}</span>
            <span class="title">${track.title}</span>
            <span class="artist">${track.artist}</span>
        `;
        list.appendChild(li);
    });
}