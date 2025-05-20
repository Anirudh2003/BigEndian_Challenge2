import asyncio
import subprocess
import sys

async def run_client(username):
    # Run client.py as a subprocess with the username argument
    proc = await asyncio.create_subprocess_exec(
        sys.executable, '-m', 'client.client',
        '--username', username,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    out = stdout.decode().strip()
    err = stderr.decode().strip()

    if proc.returncode == 0:
        print(f"[{username}] Success:\n{out}")
    else:
        print(f"[{username}] Error (code {proc.returncode}):\n{err}")

async def main():
    tasks = []
    for i in range(1, 21):
        username = f'user{i}'
        tasks.append(run_client(username))
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
