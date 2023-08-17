from xled_plus.effect_base import Effect
from xled_plus.ledcolor import image_to_led_rgb


class PictureEffect(Effect):
    def __init__(self, ctr, frame, fit='stretch'):
        # fit can be: 'stretch', 'small', 'large', 'medium'
        super(PictureEffect, self).__init__(ctr)
        self.im = frame
        self.xmid = (self.im.size[0] - 1) / 2.0
        self.ymid = (self.im.size[1] - 1) / 2.0
        if fit == 'stretch':
            self.xscale = self.im.size[0] - 1
            self.yscale = self.im.size[1] - 1
        else:
            bounds = ctr.get_layout_bounds()
            xdiff = bounds["bounds"][0][1] - bounds["bounds"][0][0]
            if xdiff == 0.0:
                xdiff = 1.0
            if fit == 'small':
                fact = max((self.im.size[0] - 1) / xdiff, self.im.size[1] - 1)
            elif fit == 'large':
                fact = min((self.im.size[0] - 1) / xdiff, self.im.size[1] - 1)
            else:
                fact = ((self.im.size[0] - 1) * (self.im.size[0] - 1) / xdiff) ** 0.5
            self.xscale = xdiff * fact
            self.yscale = fact
        if "is_animated" in dir(self.im) and self.im.is_animated:
            self.preferred_fps = 100.0 / self.im.info["duration"]
            self.preferred_frames = self.im.n_frames
        else:
            self.preferred_fps = 1
            self.preferred_frames = 1

    def get_color(self, pos):
        coord = (int(round((pos[0] - 0.5) * self.xscale + self.xmid)),
                 int(round((0.5 - pos[1]) * self.yscale + self.ymid)))
        if 0 <= coord[0] < self.im.size[0] and 0 <= coord[1] < self.im.size[1]:
            if self.im.mode == 'P':
                pix = self.im.getpixel(coord)
                rgb = self.im.getpalette()[pix * 3:pix * 3 + 3]
            elif self.im.mode == 'L':
                rgb = [self.im.getpixel(coord)] * 3
            else:
                rgb = self.im.getpixel(coord)[0:3]
        else:
            rgb = (0, 0, 0)
        return image_to_led_rgb(*rgb)

    def reset(self, numframes):
        self.index = -1

    def getnext(self):
        if "is_animated" in dir(self.im) and self.im.is_animated:
            self.index += 1
            self.im.seek(self.index % self.im.n_frames)
        return self.ctr.make_layout_pattern(self.get_color, style="square")