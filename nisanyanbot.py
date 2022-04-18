from typing import List

from telegram.ext import Updater
from telegram.ext import InlineQueryHandler
from bs4 import BeautifulSoup
import requests
import logging
from telegram import InlineQueryResultArticle, InputTextMessageContent

updater = Updater(token='TOKEN')
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

SEARCH_URL = 'https://www.nisanyansozluk.com/?k='
NOT_FOUND_DESCRIPTION = 'Nişanyan Sözlük - Çağdaş Türkçenin Etimolojisi'


def inline_nisanyan(update, context):
    query = update.inline_query.query
    results = get_results(word=query)
    context.bot.answer_inline_query(update.inline_query.id, results)


inline_nisanyan_handler = InlineQueryHandler(inline_nisanyan)
dispatcher.add_handler(inline_nisanyan_handler)
updater.start_polling()


################################################################
#                           HELPERS   
################################################################

print("hello world")
print("kotu oldugu icin ozur dilerim xd")

def get_results(word: str) -> List[InlineQueryResultArticle]:
    results = list()
    first_result = find_description(word)
    if first_result == NOT_FOUND_DESCRIPTION:
        # Let's try whether the word has homonyms(eşsesli in Turkish)
        first_result_word = f"{word}1"
        homonymous_result = find_description(first_result_word)
        if homonymous_result == NOT_FOUND_DESCRIPTION:
            # Word does not exist in Nisanyan
            results.append(return_not_found_word(word))
            return results
        results.append(return_valid_result(first_result_word, homonymous_result))
        results = try_result_homonyms(word, results)
    else:
        results.append(return_valid_result(word, first_result))
    return results


def find_description(word: str) -> str:
    search_page = soup_search(word)
    metas = search_page.find_all('meta')
    return [meta.attrs['content'] for meta in metas if 'property' in meta.attrs and
            meta.attrs['property'] == 'og:description'][0].encode('latin-1').decode('utf-8')


def soup_search(search_term: str) -> BeautifulSoup:
    url = SEARCH_URL + search_term
    response = requests.get(url)
    return BeautifulSoup(response.text, 'html.parser')


def return_valid_result(word: str, result: str) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=word,
        title=f"{word} - {result[:100]}",
        input_message_content=InputTextMessageContent(word + ': \n' + result)
    )


def return_not_found_word(word: str) -> InlineQueryResultArticle:
    return InlineQueryResultArticle(
        id=word,
        title=f"\"{word}\" nisanyan\'da bulunamadi. Baska kelimeler var ama.",
        input_message_content=InputTextMessageContent(f"{word}:\nYok kardesim yok.")
    )


def try_result_homonyms(word: str, results: List[InlineQueryResultArticle]) -> \
        List[InlineQueryResultArticle]:
    """
    Try finding all homonyms of the word in Nisanyan
    :param word: the word to search
    :param results: List of InlineQueryResultArticle
    :return: result list of InlineQueryResultArticle after homonyms search
    """
    i = 2
    while True:
        query = f"{word}{i}"
        result = find_description(query)
        if result == NOT_FOUND_DESCRIPTION:
            break
        results.append(return_valid_result(query, result))
        i += 1
    return results
