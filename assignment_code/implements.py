import math
import random
import time

import config

import pygame
from pygame.locals import Rect, K_LEFT, K_RIGHT

ITEMS = []

class Basic:
    def __init__(self, color: tuple, speed: int = 0, pos: tuple = (0, 0), size: tuple = (0, 0)):
        self.color = color
        self.rect = Rect(pos[0], pos[1], size[0], size[1])
        self.center = (self.rect.centerx, self.rect.centery)
        self.speed = speed
        self.start_time = time.time()
        self.dir = 270

    def move(self):
        dx = math.cos(math.radians(self.dir)) * self.speed
        dy = -math.sin(math.radians(self.dir)) * self.speed
        self.rect.move_ip(dx, dy)
        self.center = (self.rect.centerx, self.rect.centery)


class Paddle(Basic):
    def __init__(self):
        super().__init__(config.paddle_color, 0, config.paddle_pos, config.paddle_size)
        self.start_pos = config.paddle_pos
        self.speed = config.paddle_speed
        self.cur_size = config.paddle_size

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def move_paddle(self, event: pygame.event.Event):
        if event.key == K_LEFT and self.rect.left > 0:
            self.rect.move_ip(-self.speed, 0)
        elif event.key == K_RIGHT and self.rect.right < config.display_dimension[0]:
            self.rect.move_ip(self.speed, 0)


class Ball(Basic):
    def __init__(self, pos: tuple = config.ball_pos):
        super().__init__(config.ball_color, config.ball_speed, pos, config.ball_size)
        self.power = 1
        self.dir = 90 + random.randint(-45, 45)

    def draw(self, surface):
        pygame.draw.ellipse(surface, self.color, self.rect)

    def collide_block(self, blocks: list, items: list):  # items를 인자로 받도록 수정
        for block in blocks:
            if self.rect.colliderect(block.rect) and block.alive:  # 블록과 충돌한 경우
                # 블록 상하 충돌 처리
                if self.rect.centerx > block.rect.left and self.rect.centerx < block.rect.right:
                    if self.rect.top < block.rect.bottom and self.rect.bottom > block.rect.top:
                        block.collide(items)  # items를 전달
                        blocks.remove(block)
                        self.dir = 360 - self.dir  # 상하 벽에서 반사
                # 블록 좌우 충돌 처리
                elif self.rect.centery > block.rect.top and self.rect.centery < block.rect.bottom:
                    if self.rect.left < block.rect.right and self.rect.right > block.rect.left:
                        block.collide(items)  # items를 전달
                        blocks.remove(block)
                        self.dir = 180 - self.dir  # 좌우 벽에서 반사
                break

    def collide_paddle(self, paddle, BALLS):
        if self.rect.colliderect(paddle.rect):  # 공과 패들 충돌 처리
          if self.color == (255, 0, 0):  # 빨간색 공일 때
              BALLS.append(Ball(pos=(paddle.rect.centerx, paddle.rect.top - 10)))  # 새로운 공을 패들 위에 생성
          self.rect.bottom = paddle.rect.top  # 공이 패들 위로 올라가도록 위치 조정
          # 공이 패들과 충돌 시 방향을 반전하고 약간 랜덤하게 변화
          self.dir = 360 - self.dir + random.randint(-5, 5)
          if self in ITEMS:
              ITEMS.remove(self)  # 아이템 제거

    def adjust_direction(self, paddle):
        # 공이 패들과 충돌하면 패들이 위치한 방향으로 공을 이동시킴
        if self.rect.centerx > paddle.rect.centerx:
            # 오른쪽 방향으로 벗어나면, 왼쪽으로
            self.dir += random.randint(0, 45)  # 약간의 랜덤성 추가
        else:
            # 왼쪽 방향으로 벗어나면, 오른쪽으로
            self.dir -= random.randint(0, 45)  # 약간의 랜덤성 추가

    def hit_wall(self):
        # 좌우 벽 충돌
        if self.rect.left <= 0 or self.rect.right >= config.display_dimension[0]:
            self.dir = 180 - self.dir  # 좌우 벽에서 반사
            self.rect.clamp_ip(Rect(0, 0, config.display_dimension[0], config.display_dimension[1]))

        # 상단 벽 충돌
        if self.rect.top <= 0:
            self.dir = -self.dir  # 상단 벽에서 반사
            self.rect.clamp_ip(Rect(0, 0, config.display_dimension[0], config.display_dimension[1]))

    def alive(self):
        # 공이 화면 밖으로 빠져나갔으므로 False 반환
        if self.rect.top > config.display_dimension[1]:
            return False
        return True  # 공이 화면 안에 남아있으면 True 반환


class ItemBall(Ball):  # Ball을 상속받아서 아이템용 클래스를 확장
    def __init__(self, color, position):  # 크기 기본값을 20x20으로 설정
        super().__init__()  # 부모 클래스인 Ball의 초기화 함수 호출
        self.rect.center = position
        self.color = color  # 아이템의 색상 설정
        self.speed = 5  # 아이템의 속도
        self.size=(20, 20)
        self.rect.size=self.size

    def draw(self, surface):
        pygame.draw.ellipse(surface, self.color, self.rect)

    def move(self):
        # 아이템이 화면에서 떨어지지 않게 제한
        if self.rect.top < config.display_dimension[1]:
            self.rect.y += self.speed
        else:
            self.kill()  # 아이템이 화면 밖으로 나가면 제거

    def kill(self):  
        # 아이템이 화면 밖으로 나가면 목록에서 제거
        if self in ITEMS:
            ITEMS.remove(self)

    def collide_paddle(self, paddle: Paddle, balls: list):  # 패들과 충돌 시 공을 하나 더 추가
      if self.rect.colliderect(paddle.rect):  # 패들과 충돌했을 때
          if self.color == (255, 0, 0):  # 빨간색 공을 먹었을 때만
              new_ball = Ball(pos=(paddle.rect.centerx, paddle.rect.top - 10))  # 새로운 공 생성
              balls.append(new_ball)  # 새로운 공을 balls 리스트에 추가

          if self in ITEMS:  # self가 ITEMS에 있는지 확인
              ITEMS.remove(self)  # 아이템 제거




class Block(Basic):
    def __init__(self, color: tuple, pos: tuple = (0, 0), alive=True):
        super().__init__(color, 0, pos, config.block_size)
        self.pos = pos
        self.alive = alive

    def draw(self, surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect)

    def collide(self, items: list):  # items를 인자로 받도록 수정
        self.alive = False

        # 20% 확률로 아이템 생성
        if random.random() < 1.0:  # 20% 확률로 아이템 생성
            item_color = (255, 0, 0) if random.random() < 0.5 else (0, 0, 255)  # 빨강/파랑
            item = ItemBall(item_color, self.rect.center)  # ItemBall 클래스를 사용하여 아이템 생성
            items.append(item)
