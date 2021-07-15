#!/usr/bin/env python
import asyncio
from pathlib import Path

from copy import deepcopy

from tqdm import tqdm
import httpx

location = 'bgs'

def tasks_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task

    return [sem_task(task) for task in tasks]

async def download_card_image(client, card_id):
    path = Path(f"{card_id}.png")
    try:
        with path.open("xb") as f:
            async with client.stream("GET", f"https://art.hearthstonejson.com/v1/{location}/latest/enUS/256x/{card_id}.png") as r:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)
    except FileExistsError:
        pass

async def main():
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.hearthstonejson.com/v1/latest/enUS/cards.json"
        )

        cards = r.json()
        bg_cards = []

        for card in cards:
            if card["set"] == "BATTLEGROUNDS":
                bg_cards.append(card)
            try:
                if card["battlegroundsPremiumDbfId"] != None:
                    # print(card["name"])
                    bg_cards.append(card)
            except:
                pass
        
        bg_cards.sort(key=lambda x : x["name"])
        
        # for card in bg_cards:
        #     print(card)
        
        tasks = tasks_with_concurrency(10, *(download_card_image(client, card["id"]) for card in bg_cards))
        for t in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await t

asyncio.run(main())
