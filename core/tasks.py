import logging
import traceback
from threading import Thread

from celery import shared_task

from core.scripts import VerifyEmail

log = logging.getLogger(__name__)


@shared_task
def add(x, y):
    return x + y


def verify_email(data: dict, counter: int):
    """
    This function verify email of a single email address
    :param data: {'email': The email to be verified}
    :return:
    """
    log.info(f'Verifying email of number {str(counter)}')
    email = data.get('email')
    try:
        verify_email_obj = VerifyEmail(email)
        final_return = verify_email_obj.verify()
        is_email_valid = final_return.get('deliverable')
        data['is_email_valid'] = is_email_valid
        data.update(final_return)
        log.info(f'results for {str(email)} is : {str(is_email_valid)}')
    except Exception:
        data['is_email_valid'] = False
        log.info(f'This email has failed. {str(email)}')
        logging.error(traceback.format_exc())


@shared_task
def verify_email_list(data_list):
    """
    This function populates the contents of uploaded json data to the model
    :param data_list: A list of dictionaries containing email information
    :return:
    """
    log.info('Starting email verification for list')
    len_data = len(data_list)
    thread_list = []
    for counter, data in enumerate(data_list):
        t = Thread(target=verify_email, args=(data, counter))
        log.info(f'Verifying data number {str(counter + 1)} out of {len_data}')
        t.start()

        thread_list.append(t)
    for counter, thread in enumerate(thread_list):
        thread.join()
    return data_list
