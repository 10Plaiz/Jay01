import requests


def ocr_space_file(filename, api_key, overlay=False, language='eng'):
    """ OCR.space API request with local file.
    :param filename: Your file path & name.
    :param api_key: OCR.space API key.
    :param overlay: Is OCR.space overlay required in your response.
    :param language: Language code.
    :return: Result in JSON format.
    """
    payload = {'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               }
    try:
        with open(filename, 'rb') as f:
            r = requests.post('https://api.ocr.space/parse/image',
                              files={filename: f},
                              data=payload,
                              timeout=30)
            r.raise_for_status()
            return r.content.decode()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return "{}"


def ocr_space_url(url, api_key, overlay=False, language='eng'):
    """ OCR.space API request with remote file.
    :param url: Image url.
    :param api_key: OCR.space API key.
    :param overlay: Is OCR.space overlay required in your response.
    :param language: Language code.
    :return: Result in JSON format.
    """
    payload = {'url': url,
               'isOverlayRequired': overlay,
               'apikey': api_key,
               'language': language,
               }
    try:
        r = requests.post('https://api.ocr.space/parse/image',
                          data=payload,
                          timeout=30)
        r.raise_for_status()
        return r.content.decode()
    except requests.exceptions.RequestException as e:
        print(f"API Request failed: {e}")
        return "{}"
