def get_admin_html(user_count, admin_secret, users_table_html):
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lenner Műhely Admin Panel</title>
    <style>
        body {{ font-family: Arial; background: #121212; color: #fff; padding: 20px; margin: 0; }}
        .header-container {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        h1, h2 {{ color: #FF8C00; margin: 0; }}
        
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; background: #1E1E1E; }}
        th, td {{ border: 1px solid #444; padding: 10px; text-align: left; vertical-align: middle; }}
        th {{ background: #222; }}
        
        .card {{ background: #1E1E1E; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        input, button {{ padding: 8px; margin: 4px 0; background: #222; color: #fff; border: 1px solid #FF8C00; border-radius: 4px; }}
        button {{ background: #FF8C00; color: #000; font-weight: bold; cursor: pointer; }}
        
        .btn-delete {{ background: #C0392B; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; }}
        .btn-delete:hover {{ background: #E74C3C; }}

        .btn-clear-chat {{ background: #8E44AD; color: #fff; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold; margin-right: 5px; }}
        .btn-clear-chat:hover {{ background: #9B59B6; }}

        .btn-log {{ background: #FF8C00; color: #000; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; cursor: pointer; margin-left: 8px; }}
        .btn-log:hover {{ background: #FFA500; }}

        /* "Adatok" fül narancssárga gomb stílusa */
        .btn-title-tab {{ background: #FF8C00; color: #000; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold; cursor: pointer; margin-left: 6px; }}
        .btn-title-tab:hover {{ background: #FFA500; }}

        .sound-toggle-btn {{ background: #222; color: #FF8C00; border: 1px solid #FF8C00; padding: 8px 15px; font-weight: bold; border-radius: 6px; cursor: pointer; }}

        .user-row-wrapper {{
            position: relative;
            display: flex;
            align-items: center;
        }}
        .status-dot {{
            position: absolute;
            left: -22px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        .status-online {{ background-color: #2ECC71; box-shadow: 0 0 8px #2ECC71; }}
        .status-offline {{ background-color: #E74C3C; }}

        /* Az Adatok lenyíló panel stílusa a soron belül */
        .data-panel {{
            display: none;
            background: #181818;
            border: 1px solid #FF8C00;
            padding: 10px;
            margin-top: 8px;
            border-radius: 6px;
            color: #ddd;
            font-size: 14px;
        }}

        #log-sidebar {{
            position: fixed; top: 20px; right: 20px; width: 440px; height: calc(100vh - 100px);
            background: #1A1A1A; border: 2px solid #FF8C00; border-radius: 10px; display: none;
            flex-direction: column; box-shadow: 0 5px 25px rgba(0,0,0,0.8); z-index: 999;
        }}
        #log-header {{
            background: #222; padding: 12px 15px; color: #FF8C00; font-weight: bold;
            display: flex; justify-content: space-between; align-items: center;
            border-top-left-radius: 8px; border-top-right-radius: 8px;
        }}
        .log-header-buttons {{ display: flex; gap: 6px; align-items: center; }}
        #log-body {{ flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }}

        #bubbles-container {{
            position: fixed; bottom: 20px; right: 20px; display: flex; flex-direction: row-reverse; gap: 10px; z-index: 1000;
        }}
        .user-bubble {{
            width: 180px; height: 45px; background: #D35400; color: #fff; border-radius: 8px;
            display: flex; align-items: center; justify-content: center; font-weight: bold;
            cursor: pointer; box-shadow: 0 4px 10px rgba(0,0,0,0.5); text-align: center; font-size: 13px; padding: 5px; box-sizing: border-box;
        }}
        .blinking {{ animation: blink 1s infinite; }}
        @keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} 100% {{ opacity: 1; }} }}

        #chat-modal {{
            position: fixed; bottom: 75px; right: 20px; width: 450px; height: 480px;
            background: #1E1E1E; border: 2px solid #FF8C00; border-radius: 10px; display: none;
            flex-direction: column; box-shadow: 0 5px 15px rgba(0,0,0,0.7); z-index: 1001;
        }}
        #chat-header {{
            background: #222; padding: 10px 15px; color: #FF8C00; font-weight: bold;
            display: flex; justify-content: space-between; align-items: center; border-top-left-radius: 8px; border-top-right-radius: 8px;
        }}
        #chat-body {{ flex: 1; padding: 15px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }}
        .message-bubble {{ padding: 8px 12px; border-radius: 6px; max-width: 85%; font-size: 14px; margin-bottom: 6px; }}
        .msg-user {{ background: #333; align-self: flex-start; }}
        .msg-admin {{ background: #FF8C00; color: #000; align-self: flex-end; font-weight: bold; }}
        #chat-footer {{ padding: 10px; background: #222; display: flex; gap: 5px; }}
        #chat-footer input {{ flex: 1; }}
    </style>
    <script>
        let currentChatUser = "";
        let currentLogUser = "";
        let isChatOpen = false;
        let soundEnabled = true;

        function getStorage(key) {{
            try {{ return JSON.parse(localStorage.getItem(key)) || {{}}; }} catch(e) {{ return {{}}; }}
        }}
        function setStorage(key, val) {{
            try {{ localStorage.setItem(key, JSON.stringify(val)); }} catch(e) {{}}
        }}

        let userLastSeenCount = getStorage('userLastSeenCount');
        let persistentBubbles = getStorage('persistentBubbles');

        function playNotificationSound() {{
            if (!soundEnabled) return;
            try {{
                let AudioContext = window.AudioContext || window.webkitAudioContext;
                if (!AudioContext) return;
                let ctx = new AudioContext();
                let osc1 = ctx.createOscillator();
                let osc2 = ctx.createOscillator();
                let gain = ctx.createGain();
                osc1.type = 'sine'; osc2.type = 'sine';
                let now = ctx.currentTime;
                osc1.frequency.setValueAtTime(587.33, now);
                osc2.frequency.setValueAtTime(880, now + 0.12);
                gain.gain.setValueAtTime(0.15, now);
                gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
                osc1.connect(gain); osc2.connect(gain); gain.connect(ctx.destination);
                osc1.start(now); osc1.stop(now + 0.12);
                osc2.start(now + 0.12); osc2.stop(now + 0.35);
            }} catch(e) {{}}
        }}

        function toggleSound() {{
            soundEnabled = !soundEnabled;
            let btn = document.getElementById('sound-btn');
            if (soundEnabled) {{
                btn.innerText = "🔊 Hang: BE";
                btn.style.borderColor = "#FF8C00";
                btn.style.color = "#FF8C00";
                playNotificationSound();
            }} else {{
                btn.innerText = "🔇 Hang: KI";
                btn.style.borderColor = "#777";
                btn.style.color = "#777";
            }}
        }}

        function toggleClientRegistry() {{
            let card = document.getElementById('client-registry-card');
            if (card.style.display === 'none' || card.style.display === 'none !important' || card.style.display === '') {{
                card.style.setProperty('display', 'block', 'important');
            }} else {{
                card.style.setProperty('display', 'none', 'important');
            }}
        }}

        // Adatok panel lenyitása az adott cellán belül
        function toggleUserTitleTab(username) {{
            let panel = document.getElementById('data-panel-' + username);
            if (panel) {{
                if (panel.style.display === 'none' || panel.style.display === '') {{
                    panel.style.display = 'block';
                }} else {{
                    panel.style.display = 'none';
                }}
            }}
        }}

        window.onload = function() {{
            for (let u in persistentBubbles) {{
                if (persistentBubbles[u]) {{ createOrUpdateBubble(u, false); }}
            }}
            checkMessages();
        }};

        function checkMessages() {{
            fetch('/admin_api_messages?pass={admin_secret}')
            .then(res => res.json())
            .then(chats => {{
                let userMessages = {{}};
                chats.forEach(c => {{
                    if (c.sender !== "Lenner Műhely" && c.sender) {{
                        if (!userMessages[c.sender]) userMessages[c.sender] = [];
                        userMessages[c.sender].push(c);
                    }}
                }});
                let shouldPlaySound = false;
                for (let u in userMessages) {{
                    let count = userMessages[u].length;
                    if (!(u in userLastSeenCount) || count > userLastSeenCount[u]) {{
                        createOrUpdateBubble(u, true);
                        if (isChatOpen && currentChatUser === u) {{
                            userLastSeenCount[u] = count;
                        }} else {{
                            shouldPlaySound = true;
                        }}
                    }}
                }}
                setStorage('userLastSeenCount', userLastSeenCount);
                if (shouldPlaySound) {{ playNotificationSound(); }}
                if (isChatOpen && currentChatUser) {{
                    renderChatMessages(chats, currentChatUser);
                    if (userMessages[currentChatUser]) {{
                        userLastSeenCount[currentChatUser] = userMessages[currentChatUser].length;
                        setStorage('userLastSeenCount', userLastSeenCount);
                    }}
                }}
                let logSidebar = document.getElementById('log-sidebar');
                if (logSidebar.style.display === 'flex' && currentLogUser) {{
                    loadLoggedChats(currentLogUser);
                }}
            }}).catch(e => {{}});

            fetch('/admin_api_status?pass={admin_secret}')
            .then(res => res.json())
            .then(statuses => {{
                let tbody = document.getElementById('users-tbody');
                if (!tbody) return;
                
                for (let user in statuses) {{
                    let dot = document.getElementById('status-dot-' + user);
                    if (dot) {{
                        if (statuses[user]) {{
                            dot.className = "status-dot status-online";
                            dot.title = "Online (Aktív)";
                            dot.setAttribute('data-online', '1');
                        }} else {{
                            dot.className = "status-dot status-offline";
                            dot.title = "Offline (Inaktív)";
                            dot.setAttribute('data-online', '0');
                        }}
                    }}
                }}

                let tbodyElem = document.getElementById('users-tbody');
                let rows = Array.from(tbodyElem.querySelectorAll('tr[data-user-row]'));
                
                rows.sort((a, b) => {{
                    let dotA = a.querySelector('.status-dot');
                    let dotB = b.querySelector('.status-dot');
                    let onA = dotA ? parseInt(dotA.getAttribute('data-online') || '0') : 0;
                    let onB = dotB ? parseInt(dotB.getAttribute('data-online') || '0') : 0;

                    if (onA !== onB) {{
                        return onB - onA;
                    }}
                    let nameA = a.getAttribute('data-username').toLowerCase();
                    let nameB = b.getAttribute('data-username').toLowerCase();
                    return nameA.localeCompare(nameB);
                }});

                rows.forEach(r => tbodyElem.appendChild(r));

            }}).catch(e => {{}});
        }}

        setInterval(checkMessages, 3000);

        function createOrUpdateBubble(username, isBlinking) {{
            let container = document.getElementById('bubbles-container');
            let bubbleId = 'bubble-' + username;
            let bubble = document.getElementById(bubbleId);
            if (!bubble) {{
                bubble = document.createElement('div');
                bubble.id = bubbleId;
                bubble.className = 'user-bubble';
                bubble.onclick = function() {{ toggleUserChat(username); }};
                container.appendChild(bubble);
            }}
            if (isBlinking && (!isChatOpen || currentChatUser !== username)) {{
                bubble.innerText = "Új üzenet: " + username;
                bubble.classList.add('blinking');
            }} else {{
                bubble.innerText = username;
                bubble.classList.remove('blinking');
            }}
            persistentBubbles[username] = true;
            setStorage('persistentBubbles', persistentBubbles);
        }}

        function toggleUserChat(username) {{
            let modal = document.getElementById('chat-modal');
            let bubble = document.getElementById('bubble-' + username);
            if (isChatOpen && currentChatUser === username) {{
                modal.style.display = 'none';
                isChatOpen = false;
                if (bubble) bubble.classList.remove('blinking');
            }} else {{
                currentChatUser = username;
                document.getElementById('chat-title').innerText = "Chat: " + username;
                modal.style.display = 'flex';
                isChatOpen = true;
                if (bubble) {{
                    bubble.innerText = username;
                    bubble.classList.remove('blinking');
                }}
                fetch('/admin_api_messages?pass={admin_secret}')
                .then(res => res.json())
                .then(chats => {{
                    let uMsgs = chats.filter(c => c.sender === username);
                    userLastSeenCount[username] = uMsgs.length;
                    setStorage('userLastSeenCount', userLastSeenCount);
                    renderChatMessages(chats, username);
                    fetch('/admin?pass={admin_secret}&action=ack&user=' + encodeURIComponent(username));
                }});
            }}
        }}

        function closeChatCompletely(event) {{
            event.stopPropagation();
            let modal = document.getElementById('chat-modal');
            modal.style.display = 'none';
            isChatOpen = false;
            if (currentChatUser) {{
                let bubble = document.getElementById('bubble-' + currentChatUser);
                if (bubble) bubble.remove();
                delete persistentBubbles[currentChatUser];
                setStorage('persistentBubbles', persistentBubbles);
                currentChatUser = "";
            }}
        }}

        function toggleLoggedChats(username) {{
            let sidebar = document.getElementById('log-sidebar');
            if (sidebar.style.display === 'flex' && currentLogUser === username) {{
                sidebar.style.display = 'none';
                currentLogUser = "";
            }} else {{
                currentLogUser = username;
                document.getElementById('log-title').innerText = "Napló: " + username;
                sidebar.style.display = 'flex';
                loadLoggedChats(username);
            }}
        }}

        function loadLoggedChats(username) {{
            fetch('/admin_api_logs?pass={admin_secret}')
            .then(res => res.json())
            .then(logs => {{
                let body = document.getElementById('log-body');
                let html = '';
                let userLogs = logs.filter(msg => {{
                    let s = msg.sender || "";
                    let t = msg.target || "";
                    return s === username || t === username;
                }});
                if (userLogs.length === 0) {{
                    html = '<div style="color: #888; text-align: center; margin-top: 20px;">Nincsenek még naplózott üzenetek ehhez a felhasználóhoz.</div>';
                }} else {{
                    userLogs.forEach(msg => {{
                        let isMe = (msg.sender === "Lenner Műhely");
                        let bubbleClass = isMe ? "msg-admin" : "msg-user";
                        let senderLabel = isMe ? "Lenner Műhely" : msg.sender;
                        let timeStr = msg.timestamp ? ' [' + msg.timestamp + ']' : '';
                        html += '<div>' +
                            '<small style="display:block; font-size:10px; opacity:0.7;">' + senderLabel + timeStr + '</small>' +
                            '<div class="message-bubble ' + bubbleClass + '">' + msg.text + '</div>' +
                        '</div>';
                    }});
                }}
                body.innerHTML = html;
                body.scrollTop = body.scrollHeight;
            }});
        }}

        function saveLogAsDoc() {{
            if (!currentLogUser) return;
            fetch('/admin_api_logs?pass={admin_secret}')
            .then(res => res.json())
            .then(logs => {{
                let userLogs = logs.filter(msg => {{
                    let s = msg.sender || "";
                    let t = msg.target || "";
                    return s === currentLogUser || t === currentLogUser;
                }});
                if (userLogs.length === 0) {{
                    alert("Nincs mit menteni, ehhez a felhasználóhoz nincsenek üzenetek.");
                    return;
                }}
                let docContent = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/1999/xhtml">' +
                '<head><meta charset="utf-8"><title>Napló - ' + currentLogUser + '</title></head>' +
                '<body style="font-family: Arial, sans-serif; color: #000; padding: 20px;">' +
                    '<h2 style="color: #FF8C00;">Lenner Gumiszerviz - Naplózott Beszélgetés</h2>' +
                    '<p><strong>Ügyfél:</strong> ' + currentLogUser + '</p>' +
                    '<hr style="border: 1px solid #FF8C00;"/>' +
                    '<div style="margin-top: 20px;">';

                userLogs.forEach(msg => {{
                    let senderLabel = (msg.sender === "Lenner Műhely") ? "Lenner Műhely (Admin)" : msg.sender;
                    let timeStr = msg.timestamp ? ' - ' + msg.timestamp : '';
                    docContent += '<div style="margin-bottom: 12px; padding: 8px; background: #f4f4f4; border-left: 4px solid #FF8C00;">' +
                        '<small style="color: #666; font-size: 11px;"><strong>' + senderLabel + '</strong>' + timeStr + '</small><br/>' +
                        '<span style="font-size: 14px; display:inline-block; margin-top:4px;">' + msg.text + '</span>' +
                    '</div>';
                }});

                docContent += '</div></body></html>';

                let blob = new Blob(['\\ufeff' + docContent], {{ type: 'application/msword;charset=utf-8' }});
                let url = URL.createObjectURL(blob);
                let a = document.createElement('a');
                a.href = url;
                a.download = 'naplo_' + currentLogUser + '.doc';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }});
        }}

        function confirmDelete(username) {{
            if (confirm("Biztosan szeretnéd törölni ezt a felhasználót (" + username + ") és minden üzenetét?")) {{
                let pB = getStorage('persistentBubbles');
                delete pB[username];
                setStorage('persistentBubbles', pB);
                let uLS = getStorage('userLastSeenCount');
                delete uLS[username];
                setStorage('userLastSeenCount', uLS);
                window.location.href = '/admin?pass={admin_secret}&action=delete_user&user=' + encodeURIComponent(username);
            }}
        }}

        function confirmClearChat(username) {{
            if (confirm("Biztosan törölni szeretnéd " + username + " chatelőzményét? (A naplózott előzmények megmaradnak!)")) {{
                let pB = getStorage('persistentBubbles');
                delete pB[username];
                setStorage('persistentBubbles', pB);
                let uLS = getStorage('userLastSeenCount');
                delete uLS[username];
                setStorage('userLastSeenCount', uLS);
                window.location.href = '/admin?pass={admin_secret}&action=clear_chat&user=' + encodeURIComponent(username);
            }}
        }}

        function renderChatMessages(chats, username) {{
            let body = document.getElementById('chat-body');
            let html = '';
            chats.forEach(msg => {{
                if (msg.sender === username || (msg.sender === "Lenner Műhely" && msg.target === username)) {{
                    let isMe = (msg.sender === "Lenner Műhely");
                    let bubbleClass = isMe ? "msg-admin" : "msg-user";
                    let senderName = isMe ? "Én (Műhely)" : msg.sender;
                    let timeStr = msg.timestamp ? ' [' + msg.timestamp + ']' : '';
                    html += '<div class="message-bubble ' + bubbleClass + '">' +
                        '<small style="display:block; font-size:10px; opacity:0.7;">' + senderName + timeStr + '</small>' +
                        msg.text +
                    '</div>';
                }}
            }});
            body.innerHTML = html;
            body.scrollTop = body.scrollHeight;
        }}

        function sendAdminReply() {{
            let input = document.getElementById('reply-text');
            let text = input.value.trim();
            if(!text || !currentChatUser) return;
            fetch('/admin?pass={admin_secret}&action=reply&user=' + encodeURIComponent(currentChatUser) + '&text=' + encodeURIComponent(text))
            .then(() => {{
                input.value = '';
                fetch('/admin_api_messages?pass={admin_secret}')
                .then(res => res.json())
                .then(chats => {{
                    let uMsgs = chats.filter(c => c.sender === currentChatUser);
                    userLastSeenCount[currentChatUser] = uMsgs.length;
                    setStorage('userLastSeenCount', userLastSeenCount);
                    renderChatMessages(chats, currentChatUser);
                    let logSidebar = document.getElementById('log-sidebar');
                    if (logSidebar.style.display === 'flex' && currentLogUser === currentChatUser) {{
                        loadLoggedChats(currentLogUser);
                    }}
                }});
            }});
        }}
    </script>
</head>
<body>
    <div class="header-container">
        <h1>Lenner Gumiszerviz - Műhely Vezérlőpult</h1>
        <button id="sound-btn" class="sound-toggle-btn" onclick="toggleSound()">🔊 Hang: BE</button>
    </div>
    
    <div class="card" style="text-align: center; padding: 15px;">
        <button onclick="toggleClientRegistry()" style="background: #FF8C00; color: #000; font-size: 15px; padding: 10px 24px; border-radius: 6px; border: none; font-weight: bold; cursor: pointer;">
            📋 Ügyfél nyilvántartás ({user_count})
        </button>
    </div>

    <div id="client-registry-card" class="card" style="display: none !important;">
        <h2>Regisztrált Felhasználók ({user_count})</h2>
        <table>
            <thead>
                <tr><th>Felhasználónév</th><th>Jelszó</th><th>Üzenetek kezelése</th><th style="text-align: right;">Műveletek</th></tr>
            </thead>
            <tbody id="users-tbody">
                {users_table_html}
            </tbody>
        </table>
    </div>

    <!-- JOBB OLDALI NAPLÓZOTT BESZÉLGETÉS SÁV -->
    <div id="log-sidebar">
        <div id="log-header">
            <span id="log-title">Naplózott beszélgetés</span>
            <div class="log-header-buttons">
                <button onclick="saveLogAsDoc()" style="background: #FF8C00; color: #000; padding: 2px 10px; margin:0; font-weight:bold;">Mentés</button>
                <button onclick="let sb=document.getElementById('log-sidebar'); sb.style.display='none'; currentLogUser='';" style="background: #444; color: #fff; padding: 2px 8px; margin:0;">X</button>
            </div>
        </div>
        <div id="log-body"></div>
    </div>

    <div id="bubbles-container"></div>

    <div id="chat-modal">
        <div id="chat-header">
            <span id="chat-title">Chat</span>
            <button onclick="closeChatCompletely(event)" style="background: #444; color: #fff; padding: 2px 8px; margin:0;">X</button>
        </div>
        <div id="chat-body"></div>
        <div id="chat-footer">
            <input type="text" id="reply-text" placeholder="Írd be a választ..." onkeydown="if(event.key==='Enter') sendAdminReply();">
            <button onclick="sendAdminReply()">Küldés</button>
        </div>
    </div>

</body>
</html>"""
