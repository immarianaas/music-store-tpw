import { Injectable } from '@angular/core';
import { ActivatedRoute, ActivatedRouteSnapshot, CanActivate, Router, RouterStateSnapshot } from '@angular/router';
import { UserService } from './user.service';

@Injectable({
  providedIn: 'root'
})
export class AuthGuardService implements CanActivate{
  private isLoggedIn: boolean;

  constructor(private userService: UserService, private router: Router) {
    this.isLoggedIn = false;
    this.userService.loggedInInfo.subscribe(val => this.isLoggedIn = val);
  }

  canActivate(): boolean {
    if (!this.isLoggedIn) {
      this.router.navigate(['/']);
      return false;
    }
    return true;
  }

  public isLoggedVar(): boolean {
    return this.isLoggedIn;
  }

  public isLogged(): boolean {
    if (this.userService.username && !this.userService.existsButExpired()) return true;
    if (this.userService.existsButExpired()) this.userService.logout();
    this.router.navigate(['/login']);
    return false;
  }
}
