import requests
from bs4 import BeautifulSoup
from imdb import IMDb
from pymongo import MongoClient
from dateutil import parser


# TODO: maybe read from .env file or something similar
ia = IMDb()
client = MongoClient(
    'mongo db string goes here'
)
db = client.yms


def main():
  url = 'https://www.imdb.com/user/ur9028759/ratings'
  while url != '#':
    url = get_ratings_for_page(url)


def get_ratings_for_page(url):
  res = requests.get(url)

  if res.status_code != 200:
    print('Invalid response from imdb: ' + res.status_code)
    exit(-1)

  soup = BeautifulSoup(res.text, 'html.parser')
  ratings = soup.select('.lister-item')

  for rating in ratings:
    code = rating.select_one('.lister-item-image')['data-tconst'][2:]
    user_rating = rating.select_one('.ipl-rating-star--other-user .ipl-rating-star__rating').get_text()
    rate_date = rating.select_one('.ipl-rating-widget').findNext('p').get_text()[9:]
    insert_movie(code, user_rating, rate_date)

  return soup.select_one('.lister-page-next')['href']


def insert_movie(code, user_rating, rate_date):
  movie = ia.get_movie(code)
  dict = convert_to_dict(movie, user_rating, rate_date)
  result = db.ratings.insert_one(dict)
  print('inserted "' + dict['title'] + '" as ' + str(result.inserted_id))


def convert_to_dict(movie, user_rating, rate_date):
  return {
    'title': movie['title'] if 'title' in movie.keys() else None,
    'original_title': movie['original title'] if 'original title' in movie.keys() else None,
    'plot': [plot[:plot.index('::')] if 'plot' in movie.keys() and '::' in plot else plot for plot in movie['plot']],
    'genres': movie['genres'] if 'genres' in movie.keys() else None,
    'runtimes': movie['runtimes'] if 'runtimes' in movie.keys() else None,
    'cast': convert_persons_to_name_array(movie, 'cast') if 'cast' in movie.keys() else None,
    'released': movie['original air date'] if 'original air date' in movie.keys() else None,
    'rating': movie['rating'] if 'rating' in movie.keys() else None,
    'composers': convert_persons_to_name_array(movie, 'composers') if 'composers' in movie.keys() else None,
    'cover_art': get_max_res_poster(movie['cover url']) if 'cover url' in movie.keys() else None,
    'imdb_id': movie['imdbID'] if 'imdbID' in movie.keys() else None,
    'year': movie['year'] if 'year' in movie.keys() else None,
    'media_type': movie['kind'] if 'kind' in movie.keys() else None,
    'cinematographers': convert_persons_to_name_array(movie, 'cinematographers') if 'cinematographers' in movie.keys() else None,
    'editors': convert_persons_to_name_array(movie, 'editors') if 'editors' in movie.keys() else None,
    'director': convert_persons_to_name_array(movie, 'director') if 'director' in movie.keys() else None,
    'user_rating': user_rating,
    'rate_date': rate_date
  }


def convert_persons_to_name_array(data, tag):
  return [i['name'] for i in data[tag] if len(i.keys()) > 0]


def get_max_res_poster(url):
  start = url.index('._')
  end = url.index('.jpg')
  return url[0:start] + url[end:]


def convert_date(date_str):
  date_str = date_str[0:11]  # 06 Apr 1995
  return parser.parse(date_str)


main()