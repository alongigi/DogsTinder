function initSocket(url) {
    if (!socket) {
        socket = io.connect(url.toString(), {
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: Infinity
        });   

        socket.on( 'connect', ()=> { 
            socket.emit( 'connection', {
                receiver: current_receiver
            });
            console.log('connect fired');

            // click selected contact
            const urlParams = window.location.pathname.split('/');
            $(".contacts_body ui li[data-element='" + urlParams[2] + "']").click();

            socket.on('disconnect', function(data) {
                console.log('disconnect fired');

                current_receiver = null;
            });
        });
    } else {
        socket.socket.connect();
    }
}

function registerEvents() {
    // handle click contact
    $('.contacts_body ui li').click(function() {
        // e.preventDefault();
        clicked_receiver = this.dataset.element;
        if (clicked_receiver != current_receiver) {
            getMessagesHistory(clicked_receiver)
            .then(() => {
                // change receiver to the clicked one
                current_receiver = clicked_receiver;

                // update ui to the new chat
                const new_url = url.toString() + 'chat/' + current_receiver;
                history.pushState(current_receiver + Date.now(), "", new_url);
                $(".current_user_info").html(current_receiver);
                $(".contacts_body ui li.active").toggleClass('active');
                $(this).toggleClass('active');
                $( "#message-to-send" ).prop( "disabled", false );

                // join chat in the server
                socket.emit('join_chat', {
                    receiver : clicked_receiver
                });
            });
        }
        
        $( '#message-to-send' ).val('').focus();
    });
    
    // handle send button
    $( '.send_btn' ).click((e)=> {
        e.preventDefault();
        const user_input = $( '#message-to-send' );
        if (current_receiver && user_input.val().trim() != '') {
            socket.emit('send_message', {
            message : user_input.val()
            });
            user_input.val('').focus();
        }
    });

     // click send button when enter is pressed
     $( '#message-to-send' ).keypress((e) => {
        if ( e.which == 13 && !e.shiftKey) {
            e.preventDefault();
            $( '.send_btn' ).click();
        }
    }); 

    // handle search functionality
    $('#input-to-search').keyup(function() {
        const searchText = $(this).val().toLowerCase();
        $('.msg-list-item').filter(function() {
            //$('.msg-content', this).text().toLowerCase().indexOf(search) > -1
            $(this).toggle($('.msg-content', this).text().trim().toLowerCase().indexOf(searchText) > -1);
        });
        scrollToBottom();
    });
}

function scrollToBottom() {
    const messages = document.getElementsByClassName('msg_card_body')[0];
    messages.scrollTop = messages.scrollHeight;
}  

function addMessageToList(msg) {
    $( 'div.msg_card_body' ).append(msg);
}

async function getMessagesHistory(receiver) {
    return fetch(url + 'chat_messages/' + receiver, { 
        method: 'POST',
    })
    .then(res => res.text())
    .then(data => {
        $('.msg_card_body').html(data);
        scrollToBottom();
    })
    .catch(function(ex) {
        console.error('Error', ex.message);
    });
};

var socket;
const url = new URL('http://' + document.domain);
if (location.port != '') {
    url.port = location.port;
}
let current_receiver = null;

// init page
initSocket(url);
registerEvents();
scrollToBottom();

// when message is accepted from server
socket.on( 'message_received', function( msg ) {
    addMessageToList(msg);
    scrollToBottom();
})