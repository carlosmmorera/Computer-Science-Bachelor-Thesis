from __future__ import print_function
import base64

class email_threads:
    def __init__(self, service):
        self.service = service

    def show_chatty_threads(self, user_id='me'):
        threads = self.service.users().threads().list(userId=user_id).execute().get('threads', [])
        for thread in threads:
            tdata = self.service.users().threads().get(userId=user_id, id=thread['id']).execute()
            nmsgs = len(tdata['messages'])
    
            if nmsgs > 2:    # skip if <3 msgs in thread
                msg = tdata['messages'][0]['payload']
                subject = ''
                for header in msg['headers']:
                    if header['name'] == 'Subject':
                        subject = header['value']
                        break
                if subject:  # skip if no Subject line
                    print('- %s (%d msgs)' % (subject, nmsgs))
                    for i in range(0, nmsgs):
                        print('Message id: %s' % tdata['messages'][i]['id'])

                        #Export sections of the list headers
                        arch = open('header_sections.txt', 'w')
                        for j in range (0, len(tdata['messages'][i]['payload']['headers'])):
                            arch.write('%d.- %s\n' % (j, tdata['messages'][i]['payload']['headers'][j]['name']))
                        arch.close()

                        print('Message %s: %s'
                              % (tdata['messages'][i]['payload']['headers'][17]['name'],
                                 tdata['messages'][i]['payload']['headers'][17]['value']))
                        print('Message %s: %s'
                              % (tdata['messages'][i]['payload']['headers'][21]['name'],
                                 tdata['messages'][i]['payload']['headers'][21]['value']))
                        print('Message %s: %s'
                              % (tdata['messages'][i]['payload']['headers'][20]['name'],
                                 tdata['messages'][i]['payload']['headers'][20]['value']))
                        print('Message %s: %s'
                              % (tdata['messages'][i]['payload']['headers'][18]['name'],
                                tdata['messages'][i]['payload']['headers'][18]['value']))
                        print('Attachment: %s' % tdata['messages'][i]['payload']['filename'])
                        message = self.service.users().messages().get(userId=user_id,
                                id=tdata['messages'][i]['id'], format='raw').execute()
                        print('Message text: %s' %
                              base64.urlsafe_b64decode(message['raw'].encode('ASCII')))
                        print('------------')
                        print('------------')


                        #La posición del header depende del mensaje enviado por eso me da error
                        #No consigo obtener solo el texto del mensaje
