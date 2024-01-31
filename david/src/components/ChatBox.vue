<template>
    <div class="chat-box w-full mx-auto border border-gray-300 mt-5 overflow-hidden">
        <div class="messages-container flex flex-col p-4 overflow-y-auto" ref="messagesContainer" style="height: 300px;">
            <div v-for="(message, index) in messages" :key="index" class="message"
                :class="{ 'self-end': message.role === 'user', 'self-start': message.role !== 'user' }">
                <span class="message-content inline-block p-3 rounded-lg"
                    :class="{ 'bg-green-200': message.role === 'user', 'bg-blue-200': message.role !== 'user' }">
                    {{ message.content }}
                </span>
            </div>
        </div>
        <div class="user-input flex p-3 bg-gray-100">
            <input v-model="userInput" @keydown.capture="checkInteruption" @keyup.enter="sendMessage"
                placeholder="Type your message..."
                class="user-input-field flex-1 p-3 border border-gray-300 rounded-full mr-3" />
            <button @click="sendMessage"
                class="send-button bg-green-500 hover:bg-green-600 text-white py-2 px-6 rounded-full focus:outline-none">
                Send
            </button>
        </div>
    </div>
</template>
  
<script>
import { ref, watchEffect } from 'vue';

export default {
    name: 'ChatBox',
    props: {
        messages: {
            type: Array,
            required: true
        }
    },
    setup(props, { emit }) {
        const userInput = ref('');
        const messagesContainer = ref(null);

        const sendMessage = () => {
            if (userInput.value.trim() !== '') {
                emit('new-message', {
                    role: 'user',
                    content: userInput.value.trim()
                });
                userInput.value = '';
            }
        };

        const checkInteruption = (event) => {
            if (userInput.value.length > 6 && event.key !== 'Enter') {
                // pause video
                emit('pause-video', true);
            } else if (event.key === 'Enter' && userInput.value.trim() === '') {
                // continue playing video
                emit('pause-video', false);
            }
        };

        // Auto-scroll to the bottom of the messages container
        watchEffect(() => {
            if (messagesContainer.value) {
                const { scrollHeight, clientHeight } = messagesContainer.value;
                messagesContainer.value.scrollTop = scrollHeight - clientHeight;
            }
        });

        return {
            userInput,
            sendMessage,
            checkInteruption,
            messagesContainer,
        };
    }
};
</script>