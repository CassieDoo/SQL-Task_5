import psycopg2


def create_db(conn):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS client(
        client_id SERIAL PRIMARY KEY,
        first_name VARCHAR(40) NOT NULL,
        last_name VARCHAR(40) NOT NULL,
        email VARCHAR(40) NOT NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS phone(
        phone_id SERIAL PRIMARY KEY,
        phone_number VARCHAR(40),
        client_id INTEGER NOT NULL REFERENCES client(client_id)
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
    cur.execute("""
            INSERT INTO client (first_name, last_name, email) VALUES (%s, %s, %s) RETURNING client_id;
            """, (first_name, last_name, email))
    client_id = cur.fetchone()[0]

    while True:
        if phone_number:
            add_phone(conn, client_id, phone_number)
            phone_number = input("Введите добавляемый номер телефона: ")
        else:
            break
        conn.commit()


def add_phone(conn, client_id, phone_number):
    cur.execute("""
        INSERT INTO phone (client_id, phone_number) VALUES (%s, %s);
        """, (client_id, phone_number))
    conn.commit()


def change_client(conn, client_id, first_name=None, last_name=None, email=None, phone_number=None):
    if first_name:
        cur.execute("""
            UPDATE client SET first_name=%s WHERE client_id=%s;
            """, (first_name, client_id))
        return conn.commit()

    if last_name:
        cur.execute("""
            UPDATE client SET last_name=%s WHERE client_id=%s;
            """, (last_name, client_id))
        return conn.commit()

    if email:
        cur.execute("""
            UPDATE client SET email=%s WHERE client_id=%s;
            """, (email, client_id))
        return conn.commit()

    if phone_number:
        old_phone_number = input("Выберете номер телефона для изменения: ")
        cur.execute("""
                SELECT phone_id, client_id FROM phone
                WHERE client_id=%s AND phone_number=%s;
                """, (client_id, old_phone_number))
        phone_id = cur.fetchone()[0]

        cur.execute("""
            UPDATE phone SET phone_number=%s WHERE phone_id=%s;
            """, (phone_number, phone_id))
        return conn.commit()


def delete_phone(conn, client_id, phone_number):
    cur.execute("""
        SELECT phone_id, client_id FROM phone
        WHERE client_id=%s AND phone_number=%s;
        """, (client_id, phone_number))
    phone_id = cur.fetchone()[0]

    cur.execute("""
        DELETE FROM phone WHERE phone_id=%s;
        """, (phone_id,))
    conn.commit()


def delete_client(conn, client_id):
    cur.execute("""
        DELETE FROM phone WHERE client_id=%s;
        """, (client_id,))
    conn.commit()

    cur.execute("""
        DELETE FROM client WHERE client_id=%s;
        """, (client_id,))
    conn.commit()


def find_client(conn, first_name=None, last_name=None, email=None, phone_number=None):
    cur.execute("""
        SELECT client.client_id, client.first_name, client.last_name, client.email, phone.phone_number FROM client
        LEFT JOIN phone ON client.client_id = phone.client_id
        WHERE first_name=%s OR last_name=%s OR email=%s OR phone_number=%s;
        """, (first_name, last_name, email, phone_number))
    client = cur.fetchall()
    if not client:
        print("Клиент не найден")
    else:
        return client


with psycopg2.connect(database="clients_db", user="postgres", password="postgres") as conn:
    with conn.cursor() as cur:
        create_db(conn)

        command = input("Введите команду: ").lower()

        if command == "ac":
            print("Введите данные для добавления клиента: ")
            client_details = inuput_data()
            add_client(conn, client_details[0], client_details[1], client_details[2], client_details[3])

        else:
            print("Введите данные для поиска клиента: ")
            client_details = inuput_data()
            client = find_client(conn, client_details[0], client_details[1], client_details[2], client_details[3])

            if command == "ap":
                phone_number = input("Введите добавляемый номер телефона: ")
                add_phone(conn, client[0][0], phone_number)

            elif command == "cc":
                if client:
                    print(client)
                    print("Введите новые данные клиента:")
                    new_client_details = inuput_data()
                    change_client(conn, client[0][0], new_client_details[0], new_client_details[1],
                                  new_client_details[2], new_client_details[3])

            elif command == "dp":
                if client:
                    print(client)
                    phone_number = input("Выберете номер телефона для удаления: ")
                    delete_phone(conn, client[0][0], phone_number)

            elif command == "dc":
                if client:
                    print(client)
                    delete_client(conn, client[0][0])

            elif command == "fc":
                print(client)

            else:
                print("Неверная команда")

conn.close()
