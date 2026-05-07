let DEBUG_LOG = true;

document.addEventListener("DOMContentLoaded", function () {

    function toggleMenu(el){
        const isOpen = el.classList.contains("active");

        document.querySelectorAll(".menu-item").forEach(m => {
            m.classList.remove("active");
        });

        if(!isOpen){
            el.classList.add("active");
        }
    }

    window.toggleMenu = toggleMenu;

    document.querySelectorAll(".menu-item").forEach(item=>{
        item.addEventListener("mouseenter", ()=>{
            if(document.querySelector(".menu-item.active")){
                document.querySelectorAll(".menu-item").forEach(m=>m.classList.remove("active"));
                item.classList.add("active");
            }
        });
    });

    document.addEventListener("click", e=>{
        if(!e.target.closest(".menu")){
            document.querySelectorAll(".menu-item").forEach(m=>m.classList.remove("active"));
        }
    });

});

function log(msg){
    if(DEBUG_LOG) console.log(msg);
    serverLog("USER: " + msg);
}

function serverLog(msg){
    const box = document.getElementById("serverLogBody");
    if(!box) return;
    const time = new Date().toLocaleTimeString();
    box.innerHTML += `[${time}] ${msg}<br>`;
    box.scrollTop = box.scrollHeight;
}

function toggleServerLog(){
    document.getElementById("serverLog").classList.add("active");
}

function closeServerLog(){
    document.getElementById("serverLog").classList.remove("active");
}

function logout(){
    window.location.href = "/logout";
}

/* ABOUT */
function openAbout(){
    document.getElementById("aboutBox").style.display = "block";
    log("Opened About Box");
}

function closeAbout(){
    const box = document.getElementById("aboutBox");
    if(!box) return;

    box.style.display = "none";
    box.classList.remove("active");
}