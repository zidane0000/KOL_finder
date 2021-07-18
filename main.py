from modules.scraper import Scraper

if __name__ == '__main__':
    print('Enter target account in Instagram : ')
    target = input()
    print('Enter your username in Instagram : ')
    username = input()
    print('Enter your password in Instagram : ')
    password = input()

    scraper = Scraper(verbose=0)

    # Login
    scraper.authenticate(username, password)

    candidates = []

    # Get Expected numbers and list
    followers_num, followers_list = scraper.get_users(target, 'followers')
    following_num, following_list = scraper.get_users(target, 'following')

    # Close
    scraper.close()
