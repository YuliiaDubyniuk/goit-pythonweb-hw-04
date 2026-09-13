import asyncio
import argparse
import logging
from aiopath import AsyncPath
from aioshutil import copyfile


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


async def copy_file(file_path: AsyncPath, output_folder: AsyncPath) -> bool:
    """Copy file to subfolder based on file extension"""
    try:
        extension = file_path.suffix.lower().lstrip(".") or "no_extension"

        # create folder and file new path
        target_dir = output_folder / extension
        await target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / file_path.name

        await copyfile(file_path, target_file)
        logging.info(f"File was copied: {file_path.name} -> {target_dir}")
        return True

    except Exception as e:
        logging.error(f"Error while copying {file_path}: {e}")
        return False


async def read_folder(source_folder: AsyncPath, output_folder: AsyncPath) -> bool:
    try:
        tasks = []
        async for item in get_files(source_folder):
            tasks.append(copy_file(item, output_folder))

        if not tasks:
            logging.info("No files found to sort. Nothing was moved.")
            return True

        # run all collected coroutines concurrently
        results = await asyncio.gather(*tasks)

        return all(results)

    except Exception as e:
        logging.error(f"Error while reading directory {source_folder}: {e}")
        return False


async def get_input(prompt: str) -> str:
    """Ask folder path until user enters not empty string"""
    path = ""
    while not path:
        path = (await asyncio.to_thread(input, prompt)).strip("'\" ")
        if not path:
            print("Error: Path cannot be empty.")
    return path


async def get_files(folder: AsyncPath):
    async for item in folder.iterdir():
        if await item.is_file():
            yield item
        elif await item.is_dir():
            async for file in get_files(item):
                yield file


async def main() -> None:
    parser = argparse.ArgumentParser(description="Async file sorting by extension.")
    parser.add_argument("-s", "--source", type=str, help="Source folder path")
    parser.add_argument("-o", "--output", type=str, help="Output folder path")
    
    args = parser.parse_args()
    
    source_str = args.source or await get_input("Please enter SOURCE folder path: ")
    output_str = args.output or await get_input("Please enter OUTPUT folder path: ")
    
    source_folder = AsyncPath(source_str)
    output_folder = AsyncPath(output_str)

    if not await source_folder.exists() or not await source_folder.is_dir():
        logging.error(f"Source folder '{source_folder}' is invalid or does not exist.")
        return

    logging.info(f"Start sorting from '{source_folder}' to '{output_folder}'...")

    success = await read_folder(source_folder, output_folder)
    if success:
        logging.info("Copying and sorting completed successfully.")
    else:
        logging.warning("Copying and sorting finished with errors.")


if __name__ == "__main__":
    asyncio.run(main())
