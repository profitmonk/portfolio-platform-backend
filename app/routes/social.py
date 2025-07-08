from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.models.user import User
from app.schemas.social import (
    PostCreate, PostUpdate, PostResponse, 
    CommentCreate, CommentResponse,
    UserFollowResponse, UserProfileResponse,
    FeedResponse
)
from app.services.social_service import SocialService
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/social", tags=["Social Features"])

# Post endpoints
@router.post("/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new post"""
    post = SocialService.create_post(db, post_data, current_user.id)
    
    # Build response with author info
    response = PostResponse.from_orm(post)
    response.author_username = current_user.username
    response.author_display_name = current_user.display_name
    response.author_avatar_url = current_user.avatar_url
    response.user_has_liked = False
    
    return response

@router.get("/posts", response_model=List[PostResponse])
async def get_posts(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get posts (public or based on user access)"""
    user_id = current_user.id if current_user else None
    posts = SocialService.get_posts(db, user_id, limit, offset)
    
    # Build response with author info and like status
    response_posts = []
    for post in posts:
        post_response = PostResponse.from_orm(post)
        post_response.author_username = post.author.username
        post_response.author_display_name = post.author.display_name
        post_response.author_avatar_url = post.author.avatar_url
        
        # Check if current user has liked this post
        if current_user:
            from app.models.like import Like, LikeableType
            like_exists = db.query(Like).filter(
                Like.user_id == current_user.id,
                Like.likeable_type == LikeableType.POST,
                Like.likeable_id == post.id
            ).first()
            post_response.user_has_liked = like_exists is not None
        else:
            post_response.user_has_liked = False
        
        response_posts.append(post_response)
    
    return response_posts

@router.get("/feed", response_model=List[PostResponse])
async def get_user_feed(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get personalized feed for authenticated user"""
    posts = SocialService.get_user_feed(db, current_user.id, limit, offset)
    
    # Build response similar to get_posts
    response_posts = []
    for post in posts:
        post_response = PostResponse.from_orm(post)
        post_response.author_username = post.author.username
        post_response.author_display_name = post.author.display_name
        post_response.author_avatar_url = post.author.avatar_url
        
        # Check like status
        from app.models.like import Like, LikeableType
        like_exists = db.query(Like).filter(
            Like.user_id == current_user.id,
            Like.likeable_type == LikeableType.POST,
            Like.likeable_id == post.id
        ).first()
        post_response.user_has_liked = like_exists is not None
        
        response_posts.append(post_response)
    
    return response_posts

@router.post("/posts/{post_id}/like")
async def toggle_like_post(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Like or unlike a post"""
    # Check if post exists
    from app.models.post import Post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    is_liked = SocialService.like_post(db, post_id, current_user.id)
    return {"liked": is_liked, "message": "Post liked" if is_liked else "Post unliked"}

# Comment endpoints
@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add a comment to a post"""
    # Check if post exists
    from app.models.post import Post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    
    comment = SocialService.add_comment(db, post_id, comment_data, current_user.id)
    
    # Build response
    response = CommentResponse.from_orm(comment)
    response.author_username = current_user.username
    response.author_display_name = current_user.display_name
    response.user_has_liked = False
    response.replies = []
    
    return response

@router.get("/posts/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: int,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get comments for a post"""
    from app.models.comment import Comment
    comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.parent_comment_id.is_(None)  # Only top-level comments
    ).order_by(Comment.created_at.asc()).all()
    
    response_comments = []
    for comment in comments:
        comment_response = CommentResponse.from_orm(comment)
        comment_response.author_username = comment.author.username
        comment_response.author_display_name = comment.author.display_name
        comment_response.user_has_liked = False
        comment_response.replies = []  # TODO: Add nested replies later
        
        response_comments.append(comment_response)
    
    return response_comments

# User following endpoints
@router.post("/users/{username}/follow")
async def toggle_follow_user(
    username: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Follow or unfollow a user"""
    # Find the user to follow
    target_user = db.query(User).filter(User.username == username).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    is_following = SocialService.follow_user(db, current_user.id, target_user.id)
    return {
        "following": is_following, 
        "message": f"Now following {username}" if is_following else f"Unfollowed {username}"
    }

@router.get("/users/{username}/followers", response_model=List[UserFollowResponse])
async def get_user_followers(
    username: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get user's followers"""
    from app.models.user_follow import UserFollow
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    followers = db.query(UserFollow).filter(
        UserFollow.following_id == user.id
    ).offset(offset).limit(limit).all()
    
    return [UserFollowResponse.from_orm(follow) for follow in followers]

@router.get("/users/{username}/following", response_model=List[UserFollowResponse])
async def get_user_following(
    username: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get users that this user follows"""
    from app.models.user_follow import UserFollow
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    following = db.query(UserFollow).filter(
        UserFollow.follower_id == user.id
    ).offset(offset).limit(limit).all()
    
    return [UserFollowResponse.from_orm(follow) for follow in following]

# User profile endpoint
@router.get("/users/{username}", response_model=UserProfileResponse)
async def get_user_profile(
    username: str,
    current_user: Optional[User] = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user profile with social context"""
    current_user_id = current_user.id if current_user else None
    user = SocialService.get_user_profile(db, username, current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get featured portfolio name if exists
    featured_portfolio_name = None
    if user.featured_portfolio_id:
        from app.models.portfolio import Portfolio
        featured_portfolio = db.query(Portfolio).filter(
            Portfolio.id == user.featured_portfolio_id
        ).first()
        if featured_portfolio:
            featured_portfolio_name = featured_portfolio.name
    
    # Build response
    response = UserProfileResponse.from_orm(user)
    response.featured_portfolio_name = featured_portfolio_name
    response.is_following = getattr(user, 'is_following', False)
    response.is_followed_by = getattr(user, 'is_followed_by', False)
    
    return response
