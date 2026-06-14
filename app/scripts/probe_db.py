import asyncio

import asyncpg


async def probe_one(
    port: int, user: str, password: str, host: str = "127.0.0.1"
) -> str:
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres",
            timeout=2,
        )
        await conn.close()
        return "SUCCESS"
    except asyncpg.exceptions.InvalidPasswordError as e:
        return f"PORT_OK_BUT_PASSWORD_WRONG: {e}"
    except Exception as e:
        err_msg = str(e)
        if (
            "Connection refused" in err_msg
            or "Connect call failed" in err_msg
            or "Timed out" in err_msg
            or "timeout" in err_msg.lower()
        ):
            return "PORT_CLOSED"
        return f"OTHER_ERROR: {type(e).__name__}: {e}"


async def main() -> None:
    ports = [5432, 5433]
    hosts = ["127.0.0.1", "localhost"]
    users = ["postgres", "saleh", "admin", "root", "user", "vorgo_user", "vorgo"]
    passwords = [
        "#12345678",
        "12345678",
        "123456789",
        "123",
        "password123",
        "vorgo_pass",
        "postgres",
        "admin",
        "123456",
        "1234",
        "password",
        "",
    ]

    print("Probing local PostgreSQL ports and credentials...")
    for port in ports:
        print(f"\nProbing Port {port}:")
        port_open = False

        for host in hosts:
            for user in users:
                for pwd in passwords:
                    res = await probe_one(port, user, pwd, host)
                    if res == "SUCCESS":
                        print(
                            f"  [+] SUCCESS: host='{host}', user='{user}', password='{pwd}' works!"
                        )
                        escaped_pwd = pwd.replace("#", "%23") if "#" in pwd else pwd
                        db_url = f"postgresql+asyncpg://{user}:{escaped_pwd}@{host}:{port}/vorgo_db"
                        print("\n  [+] Set this in your .env file:")
                        print(f"      DATABASE_URL={db_url}")
                        return
                    elif res.startswith("PORT_OK_BUT_PASSWORD_WRONG"):
                        port_open = True
                        print(
                            f"  [-] Port {port} ({host}) is open, but invalid credentials: user='{user}', password='{pwd}'. Details: {res}"
                        )
                    elif res.startswith("OTHER_ERROR"):
                        print(f"  [-] Error on {host} with user='{user}': {res}")

        if not port_open:
            print(f"  [-] Port {port} appears to be closed or not running PostgreSQL.")

    print(
        "\nNo working credentials found. Please verify if PostgreSQL is running and check your password."
    )


if __name__ == "__main__":
    asyncio.run(main())
