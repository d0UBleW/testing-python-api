#!/usr/bin/env python3

import time
import random
# from typing import Optional
# from fastapi.params import Body
from fastapi import FastAPI, Response, status, HTTPException, Depends
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy.orm import Session

from . import models
from .database import engine, SessionLocal, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

class Post(BaseModel):
    title: str
    content: str
    published: bool = True

while True:
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="fastapi",
            user="admin",
            password="admin",
            cursor_factory=RealDictCursor
        )
        cursor = conn.cursor()
        print("Established connection to the database")
        break;
    except Exception as error:
        print("Failed to connect to the database")
        print(f"Error: {error}")
        time.sleep(5)


@app.get("/")
def root():
    return {"message": "Hello, World"}


@app.get("/posts")
def get_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return {"data": posts}


@app.get("/posts/{id}")
def get_post(id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == id).first()
    if post == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Unable to fetch the specified post. id does not exist")

    return {"data": post}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(post: Post, db: Session = Depends(get_db)):
    # new_post = models.Post(
    #     title=post.title,
    #     content=post.content,
    #     published=post.published
    # )

    # Convert post from pydantic model to dictionary and unpack it using `**`
    new_post = models.Post(**post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post) # Similar to `RETURNING *`
    return {"data": new_post}


@app.delete("/posts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    if post_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Unable to delete the specified post. id does not exist")

    post_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.put("/posts/{id}")
def update_post(id: int, post: Post, db: Session = Depends(get_db)):
    post_query = db.query(models.Post).filter(models.Post.id == id)
    if post_query.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Unable to update the specified post. id does not exist")

    post_query.update(post.dict(), synchronize_session=False)
    db.commit()
    return {"data": post_query.first()}
