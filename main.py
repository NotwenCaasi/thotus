import os
import sys
import asyncio
import traceback
from time import time
from asyncio import CancelledError

import numpy as np

import prompt_toolkit
from prompt_toolkit.completion import WordCompleter
#from prompt_toolkit.eventloop import use_asyncio_event_loop###

from thotus.task import Task, GuiFeedback, run_in_thread
from thotus.shell_commands import commands, toggle_advanced_mode
from thotus.commands import get_scanner
from thotus.cloudify import LineMaker
from thotus.calibration.chessboard import chess_detect, chess_draw
from thotus.ui import gui
from thotus import settings

DEBUG = os.getenv('DEBUG', False)
#use_asyncio_event_loop()###

def s2h(t):
    if t > 80:
        return "%d min %ds"%divmod(t, 60)
    else:
        return "%.1fs"%t

async def resolve(val):
    return val

class MainGUi:
    running = True
    visible = True
    line_mode = False

    async def viewer(self):
        print('D-10')###
        lm = LineMaker()
        print('D-11')###
        try:
            print('D-11a')###
            s = get_scanner()
            print('D-11b')###
            if s is None:
                raise ValueError()
        except Exception as e:
            print("Unable to init scanner, not starting viewer.")
            self.stop()
            return

        def process_image():
            img = s.cap.get(-1)
            if settings.ROTATE:
                img = np.ascontiguousarray(np.rot90(img, settings.ROTATE))
            if self.line_mode:
                lineprocessor = getattr(lm, 'from_'+settings.SEGMENTATION_METHOD)
                s.lasers_on()
                laser_image = s.cap.get(1)
                if settings.ROTATE:
                    laser_image = np.ascontiguousarray(np.rot90(laser_image, settings.ROTATE))
                s.lasers_off()
                points, processed = lineprocessor(laser_image, laser_image[:,:,0], img, img[:,:,0])
                if processed is None:
                    pass # img = black picture ??
                else:
                    img = processed
            else:
                grey = img[:,:,1]
                found, corners = chess_detect(grey)
                if found:
                    chess_draw(img, found, corners)
            return img

        while self.running:
            print('D-12')###
            if self.visible:
                print('D-12a')###
                #img = await run_in_thread(process_image) ###
                img = await resolve(run_in_thread(process_image)) ###
                print('D-12b')###
                # process display
                await gui.display(img, "live", resize=True)
                print('D-12c')###
            try:
                print('D-12d')###
                await self.wait_interval()
                print('D-12e')###
            except CancelledError:
                print('D-12f')###
                return

    async def wait_interval(self):
        await asyncio.sleep(1/60 if self.visible else 1)

    async def cli(self):
        #i_command = 0
        script_commands = []
        if len(sys.argv) > 2 and sys.argv[1] == 'exec':
            script_commands.extend(x.strip() for x in ' '.join(sys.argv[2:]).split(','))
            toggle_advanced_mode()
        #session = prompt_toolkit.shortcuts.PromptSession()###
        session = prompt_toolkit.PromptSession()###

        while self.running:
            if script_commands:
                text = script_commands.pop(0)
            else:
                try:
                    print('C-10')###
                    #text = await session.prompt(u'Scan> ', completer = WordCompleter(commands, ignore_case=True, match_middle=False), async_ = False)###
                    #text = await session.prompt(u'Scan> ', completer = WordCompleter(commands, ignore_case=True, match_middle=False), async_ = False)###
                    text = await resolve(session.prompt(u'Scan> ', completer = WordCompleter(commands, ignore_case=True, match_middle=False), async_=False))###
                    #print(text)
                    #if i_command == 1:
                    #    text = 'view'
                    #    i_command = 0
                    #i_command += 1
                    
                    print('C-11')###
                except CancelledError:
                    return
                except EOFError:
                    self.stop()
                    return

            start_execution_ts = time()
            if self.running:
                if text.strip():
                    orig_text = text
                    if ' ' in text:
                        params = text.split()
                        text = params[0]
                        params = [x.strip() for x in params[1:]]
                    else:
                        params = ()
                    text = text.strip()
                    if text == "exec":
                        script_commands[:] = [x.strip() for x in ' '.join(params).split(',') if x.strip()]
                        continue
                    try:
                        if text == "exit":
                            self.stop()
                            return
                        t = commands[text](*params)
                        if isinstance(t, GuiFeedback):
                            print('command sent')
                            t.run(self)
                        if t != 3:
                            print("")
                    except KeyboardInterrupt:
                        gui.clear()
                        print("\nAborted!")
                    except KeyError:
                        print("Command not found: %s"%text)
                    except Exception as e:
                        gui.clear()
                        print("")
                        if DEBUG:
                            traceback.print_exc()
                        else:
                            print("Error occured")
                    else:
                        duration = time() - start_execution_ts
                        if duration > 1:
                            #print("Command %s executed in %ds"%(text, s2h(duration))) ###
                            print("Command %s executed in %s"%(text, s2h(duration)))###

    async def maincoro(self):
        print('B-10')###
        self._cli = self.cli()
        print('B-11')###
        self._viewer = self.viewer()
        print('B-12')###
        self._coro = asyncio.gather(self._cli, self._viewer)
        print('B-13')###
        await self._coro
        print('B-14')###

    def stop(self):
        if not self.running:
            print("App already stopped!")
            traceback.print_exc()
        self.running = False
        self._coro.cancel()
        commands['exit']()

if __name__ == "__main__":
    app = MainGUi()
    try:
        print('A-10')###
        asyncio.get_event_loop().run_until_complete(app.maincoro())
        print('A-11')###
    except CancelledError:
        print('A-20')###
        pass
    except Exception as e:
        print('A-30')###
        traceback.print_exc()
    print("bye")
