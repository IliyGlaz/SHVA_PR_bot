import json
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload
from config import GROUP_TOKEN, USER_TOKEN  

group_vk_session = vk_api.VkApi(token=GROUP_TOKEN)  
user_vk_session = vk_api.VkApi(token=USER_TOKEN)    

group_vk = group_vk_session.get_api()
user_vk = user_vk_session.get_api()
upload = VkUpload(group_vk_session)
longpoll = VkLongPoll(group_vk_session)

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data

messages = read_json_file('messages.json')

def create_keyboard(button_text, button_text_2): ## Основная клава
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": button_text}, "color": "primary"},
                {"action": {"type": "text", "label": button_text_2}, "color": "primary"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def create_keyboard_3(): ## Клава с 3 кнопками 
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {"action": {"type": "text", "label": "Первая часть"}, "color": "primary"},
                {"action": {"type": "text", "label": "Вторая часть"}, "color": "primary"},
                {"action": {"type": "text", "label": "Третья часть"}, "color": "primary"}
            ]
        ]
    }
    return json.dumps(keyboard, ensure_ascii=False)

def send_message(user_id, message, keyboard=None):    ##отправка сообщений
    group_vk.messages.send(
        user_id=user_id,
        message=message,
        random_id=0,
        keyboard=keyboard
    )

def send_photo(user_id, image_path, message):      ## функция отправки картинок
    photo = upload.photo_messages(image_path)
    photo_id = photo[0]['id']
    photo_owner_id = photo[0]['owner_id']
    attachment = f'photo{photo_owner_id}_{photo_id}'
    empty_keyboard = '{"one_time": true, "buttons": []}'
    group_vk.messages.send(
        user_id=user_id,
        message=message,
        attachment=attachment,
        random_id=0,
        keyboard=empty_keyboard
    )


def check_subscription(user_id, group_ids):  ##Сбор подписок юзера
    try:
        response = user_vk.users.getSubscriptions(user_id=user_id, extended=1)
        groups = response['items']  # Все сообщества, включая группы и страницы
        subscribed_groups = [group['id'] for group in groups]
        return all(group_id in subscribed_groups for group_id in group_ids)

    except vk_api.VkApiError as e:
        print(f"Error checking subscriptions: {e}")
        return False

user_status = {}

for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:  
            user_id = event.user_id
            if user_id not in user_status:
                user_status[user_id] = {'checked': False}  

            if event.text.lower() == "начать": ## Проверяем подписку
                required_group_ids = [401713]  

                
                if not user_status[user_id]['checked']:  
                    if check_subscription(user_id, required_group_ids):
                        send_message(user_id, messages["начать"][0], create_keyboard_3())
                        user_status[user_id]['checked'] = True  
                    else:
                        send_message(user_id, "Пожалуйста, подпишись на нашу группу, чтобы продолжить.\n\nhttps://vk.com/atmosfera", '{"one_time": true, "buttons": []}')
                else:
                    send_message(user_id, messages["начать"][0], create_keyboard_3())

            else:
                if event.text.lower() == "конец блока" or event.text.lower() == "закончить":
                    send_message(user_id, "Вы окончили путешествие. Если хотите возобновить его, напишите \"Начать\"", '{"one_time": true, "buttons": []}')
                    continue

                if event.text.lower() == "победа" or event.text.lower() == "финал":
                    message = messages[event.text.lower()][0]
                    image_path = "Certificate.png"
                    send_photo(user_id, image_path, message)
                    continue

                if event.text.lower() == "начать":
                    message = messages["начать"][0]
                    send_message(user_id, message, create_keyboard_3())
                    continue

                if event.text.lower() in messages.keys():
                    message = messages[event.text.lower()][0]
                    button_text = messages[event.text.lower()][1]
                    button_text_2 = messages[event.text.lower()][2]
                    send_message(user_id, message, create_keyboard(button_text, button_text_2))
                else:
                    continue
