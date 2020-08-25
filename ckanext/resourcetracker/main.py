from resource import Resource

def main():
    resource = Resource('d4fe977a-a55d-4b32-8669-6957414f3f83')
    resource.data = resource.get_everything()


if __name__ == '__main__':
    main()