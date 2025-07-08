from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Optional, Dict
from fastapi import HTTPException, status

from app.models.user import User
from app.models.post import Post, PostType, Visibility
from app.models.comment import Comment
from app.models.like import Like, LikeableType
from app.models.user_follow import UserFollow
from app.models.user_preferences import UserPreferences
from app.models.feed_event import FeedEvent, EventType
from app.schemas.social import PostCreate, PostUpdate, CommentCreate

class SocialService:
    
    @staticmethod
    def create_post(db: Session, post_data: PostCreate, user_id: int) -> Post:
        """Create a new post"""
        post = Post(
            user_id=user_id,
            post_type=post_data.post_type,
            content_text=post_data.content_text,
            portfolio_id=post_data.portfolio_id,
            image_url=post_data.image_url,
            visibility=post_data.visibility,
            auto_generated=False
        )
        
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    
    @staticmethod
    def get_posts(db: Session, user_id: Optional[int] = None, limit: int = 20, offset: int = 0) -> List[Post]:
        """Get posts with visibility filtering"""
        query = db.query(Post)
        
        if user_id:
            # Authenticated user - can see public posts and posts from users they follow
            following_ids = db.query(UserFollow.following_id).filter(
                UserFollow.follower_id == user_id
            ).subquery()
            
            query = query.filter(
                or_(
                    Post.visibility == Visibility.PUBLIC,
                    and_(Post.visibility == Visibility.FOLLOWERS, Post.user_id.in_(following_ids)),
                    Post.user_id == user_id  # User's own posts
                )
            )
        else:
            # Anonymous user - only public posts
            query = query.filter(Post.visibility == Visibility.PUBLIC)
        
        return query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_user_feed(db: Session, user_id: int, limit: int = 20, offset: int = 0) -> List[Post]:
        """Get personalized feed for user"""
        # Get user's following list
        following_ids = [f.following_id for f in db.query(UserFollow).filter(
            UserFollow.follower_id == user_id
        ).all()]
        
        # Get posts from followed users and public posts
        query = db.query(Post).filter(
            or_(
                and_(Post.user_id.in_(following_ids), Post.visibility.in_([Visibility.PUBLIC, Visibility.FOLLOWERS])),
                and_(Post.visibility == Visibility.PUBLIC, Post.user_id != user_id),
                Post.user_id == user_id
            )
        )
        
        # Order by engagement score and recency
        posts = query.order_by(
            desc(Post.engagement_score),
            desc(Post.created_at)
        ).offset(offset).limit(limit).all()
        
        # Track feed view events
        for post in posts:
            SocialService.track_feed_event(db, user_id, post.id, EventType.VIEW)
        
        return posts
    
    @staticmethod
    def like_post(db: Session, post_id: int, user_id: int) -> bool:
        """Like or unlike a post"""
        existing_like = db.query(Like).filter(
            Like.user_id == user_id,
            Like.likeable_type == LikeableType.POST,
            Like.likeable_id == post_id
        ).first()
        
        if existing_like:
            # Unlike
            db.delete(existing_like)
            db.query(Post).filter(Post.id == post_id).update({
                Post.like_count: Post.like_count - 1
            })
            db.commit()
            return False
        else:
            # Like
            like = Like(
                user_id=user_id,
                likeable_type=LikeableType.POST,
                likeable_id=post_id
            )
            db.add(like)
            db.query(Post).filter(Post.id == post_id).update({
                Post.like_count: Post.like_count + 1
            })
            
            # Track engagement event
            SocialService.track_feed_event(db, user_id, post_id, EventType.LIKE)
            db.commit()
            return True
    
    @staticmethod
    def add_comment(db: Session, post_id: int, comment_data: CommentCreate, user_id: int) -> Comment:
        """Add a comment to a post"""
        comment = Comment(
            user_id=user_id,
            post_id=post_id,
            parent_comment_id=comment_data.parent_comment_id,
            content=comment_data.content
        )
        
        db.add(comment)
        
        # Update post comment count
        db.query(Post).filter(Post.id == post_id).update({
            Post.comment_count: Post.comment_count + 1
        })
        
        # Track engagement event
        SocialService.track_feed_event(db, user_id, post_id, EventType.COMMENT)
        
        db.commit()
        db.refresh(comment)
        return comment
    
    @staticmethod
    def follow_user(db: Session, follower_id: int, following_id: int) -> bool:
        """Follow or unfollow a user"""
        if follower_id == following_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot follow yourself"
            )
        
        existing_follow = db.query(UserFollow).filter(
            UserFollow.follower_id == follower_id,
            UserFollow.following_id == following_id
        ).first()
        
        if existing_follow:
            # Unfollow
            db.delete(existing_follow)
            
            # Update counts
            db.query(User).filter(User.id == follower_id).update({
                User.following_count: User.following_count - 1
            })
            db.query(User).filter(User.id == following_id).update({
                User.follower_count: User.follower_count - 1
            })
            
            db.commit()
            return False
        else:
            # Follow
            follow = UserFollow(
                follower_id=follower_id,
                following_id=following_id
            )
            db.add(follow)
            
            # Update counts
            db.query(User).filter(User.id == follower_id).update({
                User.following_count: User.following_count + 1
            })
            db.query(User).filter(User.id == following_id).update({
                User.follower_count: User.follower_count + 1
            })
            
            # Track follow event
            SocialService.track_feed_event(db, follower_id, None, EventType.FOLLOW, following_id)
            
            db.commit()
            return True
    
    @staticmethod
    def track_feed_event(db: Session, user_id: int, post_id: Optional[int], event_type: EventType, target_user_id: Optional[int] = None):
        """Track user engagement events for feed algorithm"""
        # Calculate engagement score based on event type
        engagement_scores = {
            EventType.VIEW: 1.0,
            EventType.LIKE: 5.0,
            EventType.COMMENT: 10.0,
            EventType.SHARE: 8.0,
            EventType.FOLLOW: 15.0
        }
        
        event = FeedEvent(
            user_id=user_id,
            post_id=post_id,
            target_user_id=target_user_id,
            event_type=event_type,
            engagement_score=engagement_scores.get(event_type, 1.0)
        )
        
        db.add(event)
        # Don't commit here - let the calling function handle it
    
    @staticmethod
    def get_user_profile(db: Session, username: str, current_user_id: Optional[int] = None) -> Optional[User]:
        """Get user profile with social context"""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        
        # Add relationship context if current user is provided
        if current_user_id:
            is_following = db.query(UserFollow).filter(
                UserFollow.follower_id == current_user_id,
                UserFollow.following_id == user.id
            ).first() is not None
            
            is_followed_by = db.query(UserFollow).filter(
                UserFollow.follower_id == user.id,
                UserFollow.following_id == current_user_id
            ).first() is not None
            
            # Add these as temporary attributes
            user.is_following = is_following
            user.is_followed_by = is_followed_by
        else:
            user.is_following = False
            user.is_followed_by = False
        
        return user
