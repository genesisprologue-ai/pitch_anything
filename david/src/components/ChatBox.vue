<template>
    <div class="chat-box flex flex-col pt-5 w-full">
        <div class="messages-container flex flex-col h-full" style="min-height: 200px; border: 1px solid #ccc;">
            <div v-for="(message, index) in messages" :key="index" class="message">
                <div v-if="message.role === 'user'" class="user-message">
                    {{ message.content }}
                </div>
                <div v-else class="ai-message">
                    {{ message.content }}
                </div>
            </div>
        </div>
        <div class="user-input">
            <input v-model="userInput" @keyup.enter="sendMessage" placeholder="Type your message..." />
            <button @click="sendMessage">Send</button>
        </div>
    </div>
</template>

<script>
export default {
    name: 'ChatBox',
    props: {
        messages: {
            type: Array,
            required: true
        }
    },
    data() {
        return {
            userInput: ''
        };
    },
    methods: {
        sendMessage() {
            if (this.userInput.trim() !== '') {
                this.$emit('new-message', {
                    role: 'user',
                    content: this.userInput.trim()
                });
                this.userInput = '';
            }
        }
    }
};
</script>

<style scoped>
.chat-box {
    /* Add your styles here */
}

.user-message {
    /* Add your styles here */
    float: right;
    background-color: white;
    border: 1px solid #ccc;
    margin-top: 10px;
    padding: 10px;
    margin-right: 5px;
    margin-bottom: 5px;
}

.ai-message {
    /* Add your styles here */
    float: left;
    background-color: lightblue;
    margin-top: 10px;
    margin-left: 5px;
    padding: 10px;
}

.user-input {
    /* Add your styles here */
}
</style>
