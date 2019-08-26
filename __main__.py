""" Supplementary script for writing confluence wiki articles in
vim. After specifying page details in the config.json file and posting file's
contents to replace the specified page's content.

Unless --force is specified — checks if the last author is not the one in
"author_to_check" from config.
"""
import logging
from atlassian import Confluence
import argparse
import json
import sys


def update_page_with_content(file_with_content, page_id, title,
                             confluence_instance):
    with open(file_with_content, 'r') as file_contents:
        confluence_instance.update_page(page_id, title, file_contents.read(),
                                        parent_id=None,
                                        type='page', representation='wiki',
                                        minor_edit=False)


"""Links:
* https://atlassian-python-api.readthedocs.io/en/latest/
* https://github.com/atlassian-api/atlassian-python-api
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.json",
                        help="the file with the config")
    parser.add_argument("--password", required=True,
                        help="your confluence password")
    parser.add_argument("--force", help="Force write the page, even if the last\
                        author is different", action='store_true')
    parser.add_argument("--debug", help="Enable debug logging",
                        action='store_true')
    parser.add_argument("--page_title", help="Allows overriding page title from\
                        config")
    args = parser.parse_args()

    if not args.debug:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(levelname)s %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s')

    logging.info("Checking config")

    with open(args.config, 'r') as config_file:
        poster_config = json.load(config_file)

    logging.info("Starting Confluence poster")
    if poster_config["auth"]["is_cloud"]:
        api_version = "cloud"
    else:
        api_version = "latest"
    confluence = Confluence(
        url=poster_config["auth"]["confluence_url"],
        username=poster_config["auth"]["username"],
        password=args.password,
        api_version=api_version
    )
    # Check the page_title in args
    if args.page_title:
        title = args.page_title
    else:
        title = poster_config["page"]["title"]

    page_id = confluence.get_page_id(poster_config["page"]["space"], title)

    # Check if the page was modified last by AUTHOR_TO_CHECK. If not - error
    if not args.force:
        # TODO: handle no page found
        page_update = confluence.get_page_by_id(page_id, expand="version")
        if api_version == 'cloud':
            last_updated_by = page_update['version']['by']['email']
        else:
            last_updated_by = page_update['version']['by']['username']

        if last_updated_by != poster_config["author_to_check"]:
            logging.error(f"Last author is not \
{poster_config['author_to_check']}, it's {last_updated_by}")
            logging.error(f"Please check\
{poster_config['auth']['confluence_url']}\
/pages/viewpreviousversions.action?pageId={page_id}")
            logging.error("Aborting")
            sys.exit()
        else:
            logging.info("Checked last author, it's {last_updated_by}, like in\
config, proceeding")

    # Update the page with contents from FILE_TO_OPEN
    logging.info("Updating the page")
    try:
        update_page_with_content(poster_config["file_to_open"], page_id,
                                 title, confluence)
    except Exception as e:
        logging.exception(e)
    else:
        logging.info("Update OK")


if __name__ == "__main__":
    main()
