# Friends service
Это выполнение тестового задания для стажировки в ВК.
Бэкэнд построен с использованием веб-фреймворка Django и использует фреймворк DRF для предоставления RESTful API для действий с друзьями.
Механизм подписки похож на такой же, как в социальной сети ВК.
- Если два пользователя подписываются друг на друга, то они будут отображаться как друзья.
- Если пользователь1 подписывается на пользователя2, то пользователь1 будет в подписчиках (входящий запрос) у пользователя2,
а пользователь2 в свою очередь будет в подписках (исходящий запрос) у пользователя1.

Чтобы узнать статус дружбы между клиентом (от кого запрос) и пользователем, в каждом запросе, где фигурируют данные о пользователе, есть поле `friendship_status`, которое отображает статус дружбы относительно пользователя, от которого запрос и пользователя, которого просматриваем.

Пример ниже показывает, что пользователь с `id=1` подписался на пользователя, от которого запрос.
```json
{
    "id": 1,
    "username": "admin",
    "friendship_status": "есть входящая заявка"
}
```

А этот пример показывает, что пользователь с `id=2` и пользователь, от которого запрос, подписались друг на друга.
```json
{
    "id": 2,
    "username": "admin",
    "friendship_status": "уже друзья"
}
```

## Инструкция по запуску сервиса
Чтобы запустить приложение с помощью Docker, выполните следующие шаги:
1. Соберите образ Docker с помощью команды `sudo docker build -t friends_service .`
2. Запустите контейнер с помощью команды `sudo docker run -p 8000:8000 friends_service`

Далее нужно выполнить миграции и загрузить данные из фикстуры, для этого откройте новый терминал и используйте следующие команды:
```bash
sudo docker ps
sudo docker exec -it <container_id> python manage.py migrate
sudo docker exec -it <container_id> python manage.py loaddata data.json
```
Где `<container_id>` - это идентификатор вашего контейнера Docker.

Для выполнения запросов необходимо авторизоваться. Если вы загрузили данные из фикстуры, можете использовать готовый `Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a` для запросов от имени пользователя `user1` и `id=2`. Для запросов от имени других пользователей смотрите `openapi.yaml`.

Для просмотра всех пользователей:
```
GET http://localhost:8000/api/users/
Authorization: Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a
```

Создание пользователя:
```
POST http://localhost:8000/api/users/
Content-Type: application/json

{
    "username": "new_user",
    "password": "password"
}
```

Подписаться на пользователя с `id=4`
```
POST http://localhost:8000/api/users/4/subscribe/
Authorization: Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a
```

Отписаться от пользователя с `id=4`
```
DELETE http://localhost:8000/api/users/4/subscribe/
Authorization: Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a
```

Посмотреть всех подписчиков у пользователя с `id=2`
```
GET http://localhost:8000/api/users/2/subscribers/
Authorization: Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a
```

Удалить из подписчиков пользователя с `id=4`
```
DELETE http://localhost:8000/api/users/2/subscribers/4/
Authorization: Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a
```

Посмотреть все подписки у пользователя с `id=3`
```
GET http://localhost:8000/api/users/3/subscriptions/
Authorization: Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a
```

Посмотреть всех друзей у пользователя с `id=2`
```
GET http://localhost:8000/api/users/2/friends/
Authorization: Token 9cf8aa577b69edc78fe0c1df2c2d792336c2421a
```

Полная документация запросов находиться в файле `openapi.yaml`.
