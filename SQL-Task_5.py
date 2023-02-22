import psycopg2


def create_db(conn):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client(
        client_id SERIAL PRIMARY KEY,
        first_name VARCHAR(40) NOT NULL,
        last_name VARCHAR(40) NOT NULL,
        email VARCHAR(40) NOT NULL UNIQUE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS phone(
        phone_id SERIAL PRIMARY KEY,
        phone_number VARCHAR(40) UNIQUE,
        client_id INTEGER NOT NULL REFERENCES client(client_id) ON DELETE CASCADE
    );
    """)
    conn.commit()


def inuput_data():
    first_name = input("Имя клиента: ")
    last_name = input("Фамилия клиента: ")
    email = input("email клиента: ")
    phone_number = input("Номер телефона: ")
    return [first_name, last_name, email, phone_number]


def add_client(conn, first_name, last_name, email, phone_number=None):
    if find_client(conn, email=email):
        return "Клиент с такой почтой уже существует"

    cur.execute(
        """
        INSERT INTO client (first_name, last_name, email)
        VALUES (%s, %s, %s) RETURNING client_id;
        """, (first_name, last_name, email))

    if phone_number:
        client_id = cur.fetchone()[0]

        x = add_phone(conn, client_id, phone_number)
        if x == 'Номер уже существует':
            conn.rollback()
            return "Номер уже существует, добавление невозможно"

    conn.commit()
    return "Клиент добавлен"


def add_phone(conn, client_id, phone_number):
    cur.execute("""
        SELECT phone_number FROM phone
        WHERE phone_number = %s;
        """, (phone_number,))

    if cur.fetchone():
        return "Номер уже существует"

    cur.execute("""
        INSERT INTO phone (client_id, phone_number) VALUES (%s, %s);
        """, (client_id, phone_number))

    conn.commit()
    return "Телефон добавлен"


def change_client(conn, client_id, first_name=None, last_name=None, email=None, phone_number=None):
    if first_name:
        cur.execute("""
            UPDATE client SET first_name=%s
            WHERE client_id=%s;
            """, (first_name, client_id))
        conn.commit()

    if last_name:
        cur.execute("""
            UPDATE client SET last_name=%s
            WHERE client_id=%s;
            """, (last_name, client_id))
        conn.commit()

    if email:
        cur.execute("""
            UPDATE client SET email=%s
            WHERE client_id=%s;
            """, (email, client_id))
        conn.commit()

    if phone_number:
        cur.execute("""
                SELECT phone_number FROM phone
                WHERE phone_number = %s;
                """, (phone_number,))

        if cur.fetchone():
            return "Номер уже существует"

        old_phone_number = input("Выберете номер телефона для изменения: ")
        cur.execute("""
                SELECT phone_id, client_id FROM phone
                WHERE client_id=%s AND phone_number=%s;
                """, (client_id, old_phone_number))
        phone_id = cur.fetchone()[0]

        cur.execute("""
            UPDATE phone SET phone_number=%s
            WHERE phone_id=%s;
            """, (phone_number, phone_id))
        conn.commit()

    return "Данные клиента изменены"


def delete_phone(conn, client_id, phone_number):
    cur.execute("""
        DELETE FROM phone
        WHERE client_id=%s and phone_number=%s
        RETURNING *;
        """, (client_id, phone_number))
    if not cur.fetchone():
        return "Такого номера нет"

    conn.commit()
    return "Телефон удален"

def delete_client(conn, client_id):
    cur.execute("""
        DELETE FROM client
        WHERE client_id=%s;
        """, (client_id,))

    conn.commit()
    return "Клиент удален"


def find_client(conn, first_name=None, last_name=None, email=None, phone_number=None):
    client_list = [first_name, last_name, email]
    for index, value in enumerate(client_list):
        if not value:
            client_list[index] = '%'
    phone_search = ""
    if phone_number:
        phone_search = "AND ARRAY_AGG(phone.phone_number)::TEXT[] && ARRAY[%s]"
        client_list.append(phone_number)
    query = f"""
                SELECT client.client_id, client.first_name, client.last_name, client.email,
                    CASE
                        WHEN ARRAY_AGG(phone.phone_number) = '{{Null}}' THEN ARRAY[]::TEXT[]
                        ELSE ARRAY_AGG(phone.phone_number)
                    END phone
                FROM client
                LEFT JOIN phone ON client.client_id = phone.client_id
                GROUP BY client.client_id, client.first_name, client.last_name, client.email
                HAVING client.first_name LIKE %s AND client.last_name LIKE %s AND client.email LIKE %s {phone_search};
                """
    cur.execute(
        query,
        client_list)
    return cur.fetchall()


with psycopg2.connect(database="clients_db", user="postgres", password="050700793") as conn:
    with conn.cursor() as cur:

        create_db(conn)

        command = input("Введите команду: ").lower()

        if command == "ac":
            print("Введите данные для добавления клиента: ")
            client_details = inuput_data()
            print(add_client(conn, client_details[0], client_details[1], client_details[2], client_details[3]))

        else:
            print("Введите данные для поиска клиента: ")
            client_details = inuput_data()
            client = find_client(conn, client_details[0], client_details[1], client_details[2], client_details[3])

            if command == "ap":
                phone_number = input("Введите добавляемый номер телефона: ")
                print(add_phone(conn, client[0][0], phone_number))

            elif command == "cc":
                if client:
                    print(client)
                    print("Введите новые данные клиента:")
                    new_client_details = inuput_data()
                    print(change_client(conn, client[0][0], new_client_details[0], new_client_details[1],
                                        new_client_details[2], new_client_details[3]))

            elif command == "dp":
                if client:
                    print(client)
                    phone_number = input("Выберете номер телефона для удаления: ")
                    print(delete_phone(conn, client[0][0], phone_number))

            elif command == "dc":
                if client:
                    print(client)
                    print(delete_client(conn, client[0][0]))

            elif command == "fc":
                print(client)

            else:
                print("Неверная команда")

conn.close()
