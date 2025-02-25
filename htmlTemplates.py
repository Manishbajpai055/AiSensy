css = '''
<style>
.chat-message {
    padding: 1.2rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
.stHorizontalBlock {
align-items: end !important;
}
'''

bot_template = '''
<div class="">
    <div class="message">maatsaab: {{MSG}}</div>
    <br/>
</div>
'''

user_template = '''
<div class="">
    <div class="message">User: {{MSG}}</div>
</div>
'''
